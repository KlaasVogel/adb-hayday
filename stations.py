from hd import HD
from os import path
from math import isclose
from time import sleep, time
from glob import glob
from adb import Template
import numpy as np
from logger import MyLogger,logging

class Stations(dict):
    def __init__(self, device, tasklist):
        self.log=MyLogger('Stations', LOG_LEVEL=logging.INFO)
        self.device=device
        self.tasklist=tasklist
        self.data=[]
        self.settings=[]
        self.icons=[ [],[],  #location of recipes in relation to info-button
                        [[-543, -13],[-702, 90] ], #2
                        [[-560, -95],[-715, 15],[-785, 165] ], #3
                        [[-500,-145],[-665,-77],[-800,  50],[-845,205] ], #4
                        [[-565, -15],[-700,100],[-605,-170],[-800,-75],[-915,110] ] ] #5
        self.checkListData()

    def checkListData(self):
        try:
            settings=HD.loadJSON('stations')
            resources=HD.loadJSON('resources')
            if not (len(resources) and "stations" in resources and len(settings)):
                raise Exception("Something is wrong with the loading of JSONs")

            if resources['stations']==self.data and settings==self.settings:
                return

            self.log.info("updating stations")
            self.data=resources['stations']
            self.settings=settings
            self.updateListData()
        except Exception as e:
            self.log.error(e)

    def updateListData(self):
        try:
            count={}
            for station in self.values():
                station.enabled=False
            for newstation in self.data:
                station=newstation['station']
                self.log.info(station)
                if station not in count:
                    count[station]=0
                count[station]+=1
                name=f"{station} [{count[station]}]"

                if station in self.settings:
                    data=self.settings[station]
                    products=data['recipes'].keys()
                    num_recipes=len(data['recipes'])
                    icons=self.icons[num_recipes]
                    data['icons']=dict(zip(products,icons))
                    if name not in self:
                        self[name]=Station(self.device, self.tasklist, station)
                    data['log']=MyLogger(name)
                    data['name']=name
                    data['enabled']=True
                    data['position']=HD.getPos(newstation['location'])
                    data['templates']=HD.loadTemplates('stations',station)
                    data['update']=self.checkListData
                    for key,value in data.items():
                        setattr(self[name], key, value)
                    self[name].setRecipes()
        except Exception as e:
            self.log.error(e)

    def getList(self):
        data=[]
        for name,station in self.items():
            tasks=self.tasklist.find(name)
            totaltime=self.tasklist.printtime(int(station.getTotalTime()*60))
            data.append({"name":name, "jobs": len(station.jobs), "time":totaltime, "queue":station.queue, "tasks":tasks})
        return data

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
        self.log.info(f"set recipes ({len(self.recipes)})")
        for product,recipe in self.recipes.items():
            self.products[product]=Recipe(self,product,recipe)

    #get time of last job in minutes
    def getJobTime(self):
        self.log.debug(f"\n {self.name}: getjobtime")
        self.log.debug(f"jobs: {self.jobs}")
        if len(self.jobs):
            waittime=max(self.jobs)-int(time())
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
            self.log.info(f"{self.name} new job: {product} - jobs: {self.queue}")
            self.setWaittime(wait)
            self.tasklist.addtask(wait, f"{self.name} - create: {product}", self.image, self.products[product].create)
            self.jobs.append(wait*60+int(time()))
            self.log.debug(self.jobs)
            for job in self.jobs:
                self.log.debug(f"time in seconds: {job-int(time())}\n")

    def collect(self,product,amount=1):
        x,y=[800,450]
        try:
            self.log.info(f"{self.name} collect {product}")
            if not self.reset_screen():
                raise Exception("Error on resetting Screen")

            self.move_to()
            if self.check_plus():
                self.click_green()
            location=self.device.locate_item(self.templates, self.threshold, one=True)
            if not len(location):
                raise Exception("Could not locate station")

            x,y=location
            self.device.tap(x,y)
            sleep(.2)
            self.check_cross()

            self.tasklist.removeWish(product,amount)
            self.tasklist.removeSchedule(product,amount)
            self.remove_lowest(self.jobs)
            self.orderJobs()
            self.checkJobs()
        except Exception as e:
            self.log.error(f"Could not collect {product}")
            self.log(e)
            info=f"{self.name} - retry to collect: {product}"
            self.log.info(info)
            self.tasklist.addtask(1,info, self.image, self.products[product].start_collect)
        finally:
            self.exit(x,y)

    def start(self,product,cooktime):
        try:
            self.log.info(f"{self.name} start {product}")
            icon=self.icons[product]
            recipe=self.products[product]
            x,y=[0,0]
            if not self.reset_screen():
                raise Exception("Error on resetting Screen")

            self.move_to()
            if self.check_diamond():
                self.click_green()
            self.check_moved()
            location=self.device.locate_item(self.templates, self.threshold, one=True)
            if not len(location):
                raise Exception(f"Could not find {self.name}")

            self.log.debug(f'found: {self.name}')
            x,y=location
            self.device.tap(x,y)
            sleep(.5)
            self.log.debug(f"should be open now")
            info_button=self.device.locate_item(self.info, 0.85, one=True)
            if not len(info_button):
                raise Exception(f"Could open {self.name}")

            bas=np.add(info_button,self.base)
            ico=np.add(info_button, icon)
            self.device.swipe(ico[0],ico[1],bas[0],bas[1],300)
            self.remove_lowest(self.jobs)
            sleep(.1)

            if self.check_cross(): #could not find ingredients, wait 2 minutes
                self.log.info('not enough ingredients')
                list=[]
                for ingredient in recipe.ingredients:
                    if self.onscreen(ingredient):
                        list.append(ingredient)
                if not len(list):
                    list=recipe.ingredients.keys()
                for product in list:
                    self.log.debug(f"Request: {product}")
                    self.tasklist.checkWish(product, recipe.ingredients[product])
                self.setWaittime(2)
                recipe.addJob(error=True)
                return  #exit function to reorder next item

            self.setWaittime(0)
            jobtime=self.getJobTime()+cooktime
            self.log.debug(f"new jobtime: {jobtime}")
            info=f'{self.name} - collect: {product}'
            self.log.info(info)
            self.tasklist.addtask(jobtime+0.5, info, self.image, recipe.start_collect)
            self.jobs.append(jobtime*60+int(time()))
            self.log.debug(f"jobs: {self.jobs}")
        except Exception as e:
            #something went wrong, try again in one minute
            self.log.error('something went wrong')
            self.log.error(e)
            self.log.info('retry in 1 minute')
            self.tasklist.addtask(1, f'{self.name} - create: {product}', self.image, recipe.create)
        finally:
            self.exit(x,y)

    def exit(self,x=800,y=450):
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
        if not self.station.enabled:
            return 0
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
