from hd import HD
from os import path
from math import isclose
from time import sleep, time
from glob import glob
from adb import Template

class Stations(list):
    device=None
    tasklist=None
    feed_mill={'threshold':.75,'recipes':{
        'chicken feed':{'amount':3, 'cooktime':5, 'icon': [-104,-166], 'ingredients': {'wheat': 2, 'corn':1}},
        'cow feed':{'amount':3, 'cooktime':10, 'icon': [-245,-40], 'ingredients': {'soy': 2, 'corn':1}},
        'pig feed':{'amount':3, 'cooktime':20, 'icon': [-152,-311], 'ingredients': {'carrot': 2, 'soy':1}},
        'sheep feed':{'amount':3, 'cooktime':30, 'icon': [-320,-207], 'ingredients': {'wheat': 2, 'soy':1}},
        'goat feed':{'amount':3, 'cooktime':60, 'icon': [-435,-33], 'ingredients': {}}   }}
    dairy={'threshold':.75,'recipes':{
        'cream':{'amount':1, 'cooktime':20, 'icon': [-25,-270], 'ingredients': {'milk': 1}},
        'butter':{'amount':1, 'cooktime':30, 'icon': [-185,-195], 'ingredients': {'milk': 2}},
        'cheese':{'amount':1, 'cooktime':60, 'icon': [-330,-75], 'ingredients': {'milk': 3}},
        'cheese2':{'amount':1, 'cooktime':120, 'icon': [-365,75], 'ingredients': {}}   }}
    sugar_mill={'threshold':.75,'recipes':{
        'brown sugar':{'amount':1, 'cooktime':20, 'icon': [452-565, 226-464], 'ingredients': {'sugarcane': 1}},
        'white sugar':{'amount':1, 'cooktime':40, 'icon': [295-565, 335-464], 'ingredients': {'sugarcane': 2}},
        'syrup':      {'amount':1, 'cooktime':90, 'icon': [214-565, 502-464], 'ingredients': {'sugarcane': 4}}   }}
    popcorn_pot={'threshold':.75,'recipes':{
        'popcorn':{'amount':1, 'cooktime':30, 'icon':          [-115,-235], 'ingredients': {'corn': 2}},
        'buttered popcorn':{'amount':1, 'cooktime':60, 'icon': [-265,-130], 'ingredients': {'corn':2, 'butter':1}},
        'spicy popcorn':{'amount':1, 'cooktime':60, 'icon':    [-341,   7], 'ingredients': {'corn':2, 'butter':1}}  }}
    bbq_grill={'threshold':.75,'recipes':{
        'pancake':{'amount':1, 'cooktime':30, 'icon':        [870-931, 130-413], 'ingredients': {'egg': 3, 'brown sugar':1}},
        'bacon and eggs':{'amount':1, 'cooktime':60, 'icon': [701-931, 201-413], 'ingredients': {'egg': 4,'bacon':2}},
        'hamburger':{'amount':1, 'cooktime':120, 'icon':     [569-931, 350-413], 'ingredients': {'bread':2,'bacon':2}},
        'burger2':{'amount':1, 'cooktime':180, 'icon':       [530-931, 488-413], 'ingredients': {}}  }}
    bakery={'threshold':.75,'recipes':{
        'bread':{'amount':1, 'cooktime':5, 'icon': [-60,-298], 'ingredients': {'wheat': 3}},
        'corn bread':{'amount':1, 'cooktime':30, 'icon': [-233,-228], 'ingredients': {'corn': 2, 'egg':2}},
        'cookie':{'amount':1, 'cooktime':60, 'icon': [-363,-106], 'ingredients': {'wheat': 2, 'egg':2, 'brown sugar':1}},
        'cupcake':{'amount':1, 'cooktime':120, 'icon': [-405, 48], 'ingredients': {}}   }}
    pie_oven={'threshold':.75,'recipes':{
        'carrot pie':{'amount':1, 'cooktime':60, 'icon':   [801-927, 258-416], 'ingredients': {'carrot': 3, 'egg':1, 'wheat':2}},
        'pumpkin pie':{'amount':1, 'cooktime':120, 'icon': [667-927, 376-416], 'ingredients': {'pumpkin': 3, 'egg':1, 'wheat':2}},
        'bacon pie':{'amount':1, 'cooktime':180, 'icon':   [758-927, 103-416], 'ingredients': {'bacon': 3, 'egg':1, 'wheat':2}},
        'apple pie':{'amount':1, 'cooktime':120, 'icon':   [567-927, 207-416], 'ingredients': {}},
        'paella':{'amount':1, 'cooktime':120, 'icon':      [457-927, 383-416], 'ingredients': {}} }}
    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist
        self.templates={}
    def add(self, station, location):
        position = HD.getPos(location)
        if hasattr(self,station):
            if station not in self.templates:
                self.templates[station]=HD.loadTemplates('stations',station)
            data=getattr(self,station)
            data['product']=station
            data['templates']=self.templates[station]
            data['position']=position
            self.append(Station(self.device, self.tasklist, data ))

class Station(HD):
    def __init__(self, device, tasklist, data):
        HD.__init__(self, device, tasklist, data['product'])
        for key,value in data.items():
            setattr(self, key, value)
        self.recipes={}
        self.jobs=[]
        for product,recipe in data['recipes'].items():
            self.recipes[product]=Recipe(self,product,recipe)

    def getJobTime(self):
        waittime=self.getWaitTime()
        for product in self.jobs:
            waittime+=self.recipes[product].cooktime
        return waittime

    def orderJobs(self):
        print("ordering")
        result={}
        for product in self.jobs:
            result[product]=self.recipes[product].cooktime
        self.jobs=sorted(result, key=result.get)
        print(self.jobs)

    def checkJobs(self):
        print(f"checking jobs for {self.product}")
        wait=self.getWaitTime()+0.25
        if len(self.jobs) and not self.scheduled:
            print('adding task')
            product=self.jobs.pop(0)
            print(f"new job: {product} - jobs: {self.jobs}")
            self.setWaittime(wait)
            self.tasklist.addtask(wait, product, self.image, self.recipes[product].create)
            self.scheduled=True

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
                    self.orderJobs()
                else:
                    self.tasklist.addtask(5, product, f'collect {product}', self.recipes[product].start_collect)
            self.checkJobs()
            self.move_from()
        else:
            self.tasklist.addtask(1, product, self.image, self.recipes[product].start_collect)

    def start(self,product,icon,cooktime):
        recipe=self.recipes[product]
        if self.reset_screen():
            self.move_to()
            if self.check_diamond():
                self.click_green()
            self.check_moved()
            location=self.device.locate_item(self.templates, self.threshold, one=True)
            if len(location):
                print(f'found: {self.product}')
                x,y=location
                dx,dy=icon
                self.device.tap(x,y)
                print(f"should be opened now")
                if self.check_diamond():
                    newlocation=self.device.locate_item(self.templates, self.threshold, one=True)
                    x,y = newlocation if len(newlocation) else location
                    self.device.swipe(x+dx,y+dy,x,y+215,300)
                    self.scheduled=False
                    sleep(.1)
                    if self.check_cross(): #could not find ingredients, wait 2 minutes
                        print('not enough ingredients')
                        recipe.checkIngredients()
                        self.setWaittime(2)
                        recipe.addJob(error=True)
                        self.exit(x,y)
                        return
                    self.setWaittime(cooktime)
                    self.tasklist.addtask(cooktime+0.5, f'collect {product}', self.image, recipe.start_collect)
                    self.exit(x,y)
                    return

        #something went wrong, try again in one minute
        print('something went wrong')
        sleep(0.5)
        self.tasklist.addtask(1, f'{self.product}: create {product}', self.image, recipe.create)

    def exit(self,x,y):
        self.device.tap(x-80,y-40)
        self.move_from()


class Recipe():
    def __init__(self, station, product, recipe):
        self.station=station
        self.product=product
        for key,value in recipe.items():
            setattr(self, key, value)
            station.tasklist.addProduct(product, self.addJob, station.getJobTime)

    def addJob(self,error=False):
        self.station.jobs.append(self.product)
        # self.checkIngredients()
        if not error:
            self.station.orderJobs()
        self.station.checkJobs()
        return self.amount

    def checkIngredients(self):
        for ingredient,amount in self.ingredients.items():
            self.station.tasklist.checkWish(ingredient, amount)

    def create(self):
        self.station.start(self.product, self.icon, self.cooktime)

    def start_collect(self):
        self.station.collect(self.product,self.amount)
