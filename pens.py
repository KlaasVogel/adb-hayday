from hd import HD
from os import path
from math import isclose
from time import sleep, time
from glob import glob
from adb import Template
import numpy as np
import math
from math import sin, cos, pi

class Pens(dict):
    device=None
    tasklist=None
    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist
        self.data=[]
        self.settings=[]
        self.updateListData()

    def updateListData(self):
        settings=HD.loadJSON('animals')
        resources=HD.loadJSON('resources')
        count={}
        if len(resources) and "pens" in resources and len(settings):
            if resources['pens']!=self.data or settings!=self.settings:
                self.data=resources['pens']
                self.settings=settings
                for pen in self.values():
                    pen.enabled=False
                for newpen in self.data:
                    animal=newpen['animal']
                    if animal not in count:
                        count[animal]=0
                    count[animal]+=1
                    name=f"Pen {animal} [{count[animal]}]"
                    if animal in self.settings:
                        data=self.settings[animal]
                        product=data['product']
                        if name not in self:
                            self[name]=Pen(self.device, self.tasklist, animal, product)
                        data['name']=name
                        data['enabled']=True
                        data['position']=HD.getPos(newpen['location'])
                        data['temp_pen']=HD.loadTemplates('pens',animal)
                        data['temp_collect']=HD.loadTemplates(path.join('pens','collect'),animal)
                        data['temp_food']=HD.loadTemplates(path.join('pens','food'),animal)
                        data['amount']=newpen['amount']
                        data['update']=self.updateListData
                        for key,value in data.items():
                            setattr(self[name], key, value)

class Pen(HD):
    pencil=HD.loadTemplates('pens','pencil')
    def __init__(self, device, tasklist, animal, product):
        HD.__init__(self, device, tasklist, product)
        self.animal=animal
        self.center=[0,0]
        self.product=product
        self.tasklist.addProduct(self.product, self.addJob, self.getJobTime)
        # self.tasklist.addtask(0.05, self.animal, self.image, self.collect)

    def getJobTime(self):
        waittime=self.getWaitTime()
        waittime+=self.jobs*self.eattime
        return waittime

    def addJob(self):
        self.jobs+=1
        # self.checkFood()
        self.checkJobs()
        return self.amount

    def checkCollected(self):
        print(f"checking if all {self.product} is collected")
        result=self.device.locate_item(self.temp_collect, self.threshold_collect)
        if len(result):
            print('not collected')
            return False
        return True

    def checkFed(self):
        print(f"checking if all {self.animal} are fed")
        result=self.device.locate_item(self.temp_food, self.threshold_food)
        if len(result):
            print('not fed')
            return False
        return True

    def checkJobs(self):
        print(f"checking jobs for {self.product}")
        wait=self.getWaitTime()+0.2
        if not self.scheduled:
            if self.jobs>0 :
                print('adding task')
                self.jobs+=-1
                self.setWaittime(wait)
                self.tasklist.addtask(wait, f"collect: {self.product}", self.image, self.collect)
                self.tasklist.addWish(self.food, self.amount)
                self.scheduled=True
                return
            # self.tasklist.reset(self.product)

    def checkFood(self):
        self.tasklist.checkWish(self.food, self.amount)

    def exit(self):
        x,y=self.center
        self.device.tap(x-150,y-80)
        self.move_from()

    def locate_pen(self):
        print("move to Pen")
        if self.reset_screen():
            self.move_to()
            location=self.device.locate_item(self.temp_pen, self.threshold, one=True)
            if len(location):
                self.center=np.add(location,self.center_offset)
                self.device.tap(*self.center)
                sleep(.3)
                pencil_loc=self.device.locate_item(self.pencil, 0.8, one=True)
                if len(pencil_loc):
                    self.center=np.add(pencil_loc,self.pencil_offset)
                    return True
        return False

    def loadPath(self):
        data=self.loadJSON('paths')
        if not len(data):
            data={'default':[[0,0]]}
        trace_path=data[self.animal] if self.animal in data else data['default']
        return np.array(trace_path)

    def createWaypoints(self,delta=[0,0]):
        trace_path=self.loadPath()
        waypoints = np.empty_like(trace_path)
        for i in range(trace_path.shape[0]):
          waypoints[i, :] = trace_path[i, :] + self.center + delta
        return waypoints.tolist()

    def execute(self,condition,icon,steps=3):
        r,theta=[0,0]
        while (not condition() and  r < 15):
            delta=[cos(theta)*r,sin(theta)*r/2]
            waypoints=self.createWaypoints(delta)
            self.trace(waypoints, *icon)
            theta+=pi/4
            if (theta > pi*0.9):
                theta=0
                r+=15/steps

    def checkMissingFood(self):
        wait=10
        if self.check_cross():
            self.setWaittime(10)
            print(f"Missing Food. retry in {wait} minutes")
            self.checkFood()
            self.tasklist.addtask(wait+.2, f'Try Feeding {self.animal}', self.image, self.feed)
            return True
        return False

    def feed(self,atsite=False):
        print('feeding')
        self.update()
        if not self.enabled:
            return
        if atsite or self.locate_pen():
            if atsite:
                self.execute(self.checkFed,self.icon_feed,steps=1)
                if self.checkMissingFood():
                    self.exit()
                    return False
            if not self.checkFed():
                print("Not all animals are fed.")
                self.execute(self.checkFed,self.icon_feed,steps=3)
                if self.checkMissingFood():
                    self.exit()
                    return False
            self.checkFood()
            self.setWaittime(self.eattime)
            self.scheduled=False
            self.checkJobs()
            self.exit()
            return True
        print('something went wrong')
        self.exit()
        self.tasklist.addtask(1, f"Feed: {self.animal}", self.image, self.feed)
        return False

    def collect(self):
        print(f'collecting: {self.product}')
        self.update()
        if not self.enabled:
            return
        if self.locate_pen():
            self.tasklist.removeSchedule(self.product,self.amount)
            self.execute(self.checkCollected,self.icon_collect)
            self.tasklist.removeWish(self.product,self.amount)
            self.setWaittime(5)
            if self.check_cross():
                print("Barn is full, need to sell something")
                print("retry in 5 minutes")
                self.tasklist.addtask(5, self.animal, self.image, self.collect)
                self.exit()
                return
            print("Collection succesfull")
            self.feed(True)
            return

        print('something went wrong')
        self.tasklist.addtask(1, self.animal, self.image, self.collect)
