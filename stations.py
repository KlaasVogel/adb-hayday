from hd import HD
from os import path
from math import isclose
from time import sleep, time
from glob import glob
from adb import Template
import numpy as np

class Stations(list):
    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist
        self.templates={}
        self.icons=[ [],[],  #location of recipes in relation to info-button
                    [[-543, -13],[-702, 90] ], #2
                    [[-560, -95],[-715, 15],[-785, 165] ], #3
                    [[-500,-145],[-665,-77],[-800,  50],[-845,205] ], #4
                    [[-565, -15],[-700,100],[-605,-170],[-800,-75],[-915,110] ] ] #5
        self.station_data=HD.loadJSON('stations')

    def add(self, station, location):
        position = HD.getPos(location)
        if station in self.station_data:
            if station not in self.templates:
                self.templates[station]=HD.loadTemplates('stations',station)
            data=self.station_data[station]
            products=data['recipes'].keys()
            num_recipes=len(data['recipes'])
            icons=self.icons[num_recipes]
            data['icons']=dict(zip(products,icons))
            data['name']=station
            data['templates']=self.templates[station]
            data['position']=position
            self.append(Station(self.device, self.tasklist, station))
            HD.setData(self[-1], data)
            self[-1].setRecipes()

class Station(HD):
    def __init__(self, device, tasklist, station):
        HD.__init__(self, device, tasklist, station)
        self.base=[-490,305]
        self.products={}
        self.queue=[]
        self.jobs=[]

    @staticmethod
    def remove_lowest(list):
        if len(list):
            lowest=min(list)
            for idx, value in enumerate(list):
                if value==lowest:
                    break
            list.pop(idx)

    def setRecipes(self):
        for product,recipe in self.recipes.items():
            self.products[product]=Recipe(self,product,recipe)

    #get time of last job in minutes
    def getJobTime(self):
        self.log.debug(f"\n {self.name}: getjobtime")
        self.log.debug(f"jobs: {self.jobs}")
        if len(self.jobs):
            waittime=self.jobs[-1]-int(time())
            self.log.debug(f"waittime: {waittime}")
            if waittime > 0:
                wait=int(waittime/60)
                self.log.debug(f"wait: {wait}")
                return wait
        return 0

    def getTotalTime(self):
        self.log.debug(f"\n {self.name}: gettotaltime")
        waittime=self.getWaitTime()+self.getJobTime()
        self.log.debug(f"{self.name}: waittime: {waittime}")
        for product in self.queue:
            waittime+=self.products[product].cooktime
        self.log.debug(f"{self.name}: total waittime: {waittime}")
        return waittime

    def orderJobs(self):
        self.log.debug("\n ordering")
        result={}
        for product in self.queue:
            result[product]=self.products[product].cooktime
        self.queue=sorted(result, key=result.get)
        self.log.debug(self.queue)

    def checkJobs(self):
        self.log.debug(f"\n checking jobs for {self.name}")
        wait=self.getWaitTime()+0.25
        self.log.debug(f"queue: {self.queue}")
        if len(self.queue) and len(self.jobs)<2:
            self.log.debug('adding task')
            product=self.queue.pop(0)
            self.log.debug(f"new job: {product} - jobs: {self.queue}")
            self.setWaittime(wait)
            self.tasklist.addtask(wait, f"create: {product}", self.image, self.products[product].create)
            self.jobs.append(wait*60+int(time()))
            self.log.debug(self.jobs)
            for job in self.jobs:
                self.log.debug(f"time in seconds: {job-int(time())}\n")

    def collect(self,product,amount=1):
        if self.reset_screen():
            self.move_to()
            if self.check_plus():
                self.click_green()
            location=self.device.locate_item(self.templates, self.threshold, one=True)
            if len(location):
                x,y=location
                self.device.tap(x,y)
                sleep(.2)
                if not self.check_cross():
                    self.tasklist.removeWish(product,amount)
                    self.tasklist.removeSchedule(product,amount)
                    self.jobs.pop(0)
                    self.orderJobs()
                else:
                    self.tasklist.addtask(5, product, f'collect: {product}', self.products[product].start_collect)
            self.checkJobs()
            self.move_from()
        else:
            self.tasklist.addtask(1, f"retry to collect: {product}", self.image, self.products[product].start_collect)

    def start(self,product,cooktime):
        icon=self.icons[product]
        recipe=self.products[product]
        x,y=[0,0]
        if self.reset_screen():
            self.move_to()
            if self.check_diamond():
                self.click_green()
            self.check_moved()
            location=self.device.locate_item(self.templates, self.threshold, one=True)
            if len(location):
                self.log.debug(f'found: {self.name}')
                x,y=location
                self.device.tap(x,y)
                sleep(.5)
                self.log.debug(f"should be opened now")
                info_button=self.device.locate_item(self.info, 0.85, one=True)
                if len(info_button):
                    bas=np.add(info_button,self.base)
                    ico=np.add(info_button, icon)
                    self.device.swipe(ico[0],ico[1],bas[0],bas[1],300)
                    self.remove_lowest(self.jobs)
                    sleep(.1)
                    if self.check_cross(): #could not find ingredients, wait 2 minutes
                        self.log.debug('not enough ingredients')
                        for ingredient,amount in recipe.ingredients.items():
                            if self.onscreen(ingredient):
                                self.log.debug(f"Request: {ingredient}")
                                sleep(2)
                                self.tasklist.checkWish(ingredient, amount)
                        self.setWaittime(2)
                        recipe.addJob(error=True)
                        self.exit(x,y)
                        return
                    self.setWaittime(0)
                    jobtime=self.getJobTime()+cooktime
                    self.log.debug(f"new jobtime: {jobtime}")
                    self.tasklist.addtask(jobtime+0.5, f'collect {product}', self.image, recipe.start_collect)
                    self.jobs.append(jobtime*60+int(time()))
                    self.log.debug(f"jobs: {self.jobs}")
                    sleep(5)
                    self.exit(x,y)
                    return
        #something went wrong, try again in one minute
        self.log.debug('something went wrong')
        sleep(0.3)
        self.exit(x,y)
        self.tasklist.addtask(1, f'{self.name}: create {product}', self.image, recipe.create)

    def exit(self,x,y):
        self.device.tap(x-80,y-40)
        self.move_from()


class Recipe():
    def __init__(self, station, product, recipe):
        self.station=station
        self.product=product
        for key,value in recipe.items():
            setattr(self, key, value)
            station.tasklist.addProduct(product, self.addJob, station.getTotalTime)

    def addJob(self,error=False):
        self.station.queue.append(self.product)
        if not error:
            self.requestIngredients()
            self.station.orderJobs()
        self.station.checkJobs()
        return self.amount

    def requestIngredients(self):
        for ingredient,amount in self.ingredients.items():
            self.station.tasklist.addWish(ingredient, amount)

    def create(self):
        self.station.start(self.product, self.cooktime)

    def start_collect(self):
        self.station.collect(self.product, self.amount)
