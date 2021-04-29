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
        'chicken feed':{'amount':3, 'cooktime':5, 'icon': [-50,-300], 'ingredients': {'wheat': 2, 'corn':1}},
        'cow feed':{'amount':3, 'cooktime':10, 'icon': [-220,-230], 'ingredients': {'soy': 2, 'corn':1}},
        'pig feed':{'amount':3, 'cooktime':20, 'icon': [-350,-110], 'ingredients': {'carrot': 2, 'soy':1}},
        'sheep feed':{'amount':3, 'cooktime':40, 'icon': [-390,50], 'ingredients': {}}   }}
    dairy={'threshold':.75,'recipes':{
        'cream':{'amount':1, 'cooktime':20, 'icon': [-15,-250], 'ingredients': {'milk': 1}},
        'butter':{'amount':1, 'cooktime':30, 'icon': [-185,-175], 'ingredients': {'milk': 2}},
        'cheese':{'amount':1, 'cooktime':60, 'icon': [-325,-55], 'ingredients': {'milk': 3}},
        'cheese2':{'amount':1, 'cooktime':120, 'icon': [-365,90], 'ingredients': {}}   }}
    sugar_mill={'threshold':.75,'recipes':{
        'brown sugar':{'amount':1, 'cooktime':20, 'icon': [-95,-220], 'ingredients': {'sugarcane': 1}},
        'white sugar':{'amount':1, 'cooktime':40, 'icon': [-265, -105], 'ingredients': {'sugarcane': 2}}   }}
    popcorn_pot={'threshold':.75,'recipes':{
        'popcorn':{'amount':1, 'cooktime':30, 'icon': [-135,-155], 'ingredients': {'corn': 2}},
        'pop2':{'amount':1, 'cooktime':120, 'icon': [-270,-25], 'ingredients': {}}   }}
    bbq_grill={'threshold':.75,'recipes':{
        'pancake':{'amount':1, 'cooktime':30, 'icon': [-127,-230], 'ingredients': {'egg': 3, 'brown sugar':1}},
        'bacon and eggs':{'amount':1, 'cooktime':60, 'icon': [-285,-120], 'ingredients': {'egg': 4,'bacon':2}},
        'burger':{'amount':1, 'cooktime':120, 'icon': [-345, 25], 'ingredients': {}}   }}
    bakery={'threshold':.75,'recipes':{
        'bread':{'amount':1, 'cooktime':5, 'icon': [-70,-270], 'ingredients': {'wheat': 3}},
        'cake':{'amount':1, 'cooktime':30, 'icon': [-240,-210], 'ingredients': {'corn': 2, 'egg':2}},
        'cookie':{'amount':1, 'cooktime':60, 'icon': [-370,-85], 'ingredients': {'wheat': 2, 'egg':2, 'brown sugar':1}},
        'cupcake':{'amount':1, 'cooktime':120, 'icon': [-415, 65], 'ingredients': {}}   }}
    pie_oven={'threshold':.75,'recipes':{
        'carrot pie':{'amount':1, 'cooktime':60, 'icon': [-128,-248], 'ingredients': {'carrot': 3, 'egg':1, 'wheat':2}},
        'pumpkin pie':{'amount':1, 'cooktime':120, 'icon': [-286,-141], 'ingredients': {'pumpkin': 3, 'egg':1, 'wheat':2}},
        'apple pie':{'amount':1, 'cooktime':0, 'icon': [-3353,6], 'ingredients': {}} }}

    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist
        self.templates={}
    def add(self, station, threshold=None, lok_x=0, lok_y=0):
        pos_x, pos_y = HD.getPos(lok_x,lok_y)
        if hasattr(self,station):
            if station not in self.templates:
                self.templates[station]=HD.loadTemplates('stations',station)
            data=getattr(self,station)
            self.append(Station(self.device, self.tasklist, station, data['recipes'], data['threshold'], self.templates[station], pos_x, pos_y ))


class Station(HD):
    def __init__(self, device, tasklist, station, recipes, threshold, templates, pos_x, pos_y):
        HD.__init__(self, device, station, tasklist, threshold, pos_x, pos_y)
        self.recipes={}
        self.templates=templates
        self.jobs=[]
        self.scheduled=False
        for product,recipe in recipes.items():
            self.recipes[product]=Recipe(self,product,recipe)

    def getJobTime(self):
        waittime=self.getWaitTime()
        for product in self.jobs:
            waittime+=self.recipes[product].cooktime
        return waittime

    def checkJobs(self):
        print(f"checking jobs for {self.product}")
        wait=self.getWaitTime()
        if len(self.jobs) and not self.scheduled:
            print('adding task')
            product=self.jobs.pop(0)
            print(f"new job: {product} - jobs: {self.jobs}")
            sleep(2)
            self.tasklist.addtask(wait/60+0.3, product, self.image, self.recipes[product].create)
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
                else:
                    self.tasklist.addtask(5, product, self.image, self.recipes[product].start_collect)
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
                    self.device.swipe(x+dx,y+dy,x,y,300)
                    self.scheduled=False
                    sleep(.1)
                    if self.check_cross(): #could not find ingredients, wait 2 minutes
                        print('not enough ingredients')
                        recipe.checkIngredients()
                        self.setWaittime(2)
                        recipe.addJob()
                        self.move_from()
                        return
                    self.setWaittime(cooktime)
                    self.tasklist.addtask(cooktime+0.5, self.product, self.image, recipe.start_collect)
                    self.click_green()
                    self.move_from()
                    return
            self.click_green()
            self.move_from()
        #something went wrong, try again in one minute
        print('something went wrong')
        sleep(2)
        self.tasklist.addtask(1, self.product, self.image, recipe.create)


class Recipe():
    def __init__(self, station, product, recipe):
        self.station=station
        self.product=product
        for key,value in recipe.items():
            setattr(self, key, value)
            station.tasklist.addProduct(product, self.addJob, station.getJobTime)

    def addJob(self):
        self.station.jobs.append(self.product)
        self.checkIngredients()
        self.station.checkJobs()
        return self.amount

    def checkIngredients(self):
        for ingredient,amount in self.ingredients.items():
            self.station.tasklist.checkWish(ingredient, amount)

    def create(self):
        self.station.start(self.product, self.icon, self.cooktime)

    def start_collect(self):
        self.station.collect(self.product,self.amount)
