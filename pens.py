from hd import HD
from os import path
from math import isclose
from time import sleep, time
from glob import glob
from adb import Template
import numpy as np
import math
from math import sin, cos, pi
from logger import MyLogger, logging

class Pens(dict):
    device=None
    tasklist=None
    def __init__(self, device, tasklist):
        self.log=MyLogger('Pens', LOG_LEVEL=logging.INFO)
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
                        data['log']=self.log
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
        if not self.enabled:
            return False
        waittime=self.getWaitTime()
        waittime+=self.jobs*self.eattime+0.1
        return waittime

    def addJob(self):
        self.jobs+=1
        # self.checkFood()
        self.checkJobs()
        return self.amount

    def checkCollected(self):
        self.log.debug(f"checking if all {self.product} is collected")
        result=self.device.locate_item(self.temp_collect, self.threshold_collect)
        if len(result):
            self.log.debug('not collected')
            return False
        return True

    def checkFed(self):
        self.log.debug(f"checking if all {self.animal} are fed")
        result=self.device.locate_item(self.temp_food, self.threshold_food)
        if len(result):
            self.log.debug('not fed')
            return False
        return True

    def checkJobs(self):
        self.log.debug(f"checking jobs for {self.product}")
        wait=self.getWaitTime()+0.2
        if not self.scheduled:
            if self.jobs>0 :
                self.log.debug('adding task')
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
        self.log.debug("move to Pen")
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
            self.log.debug(f"Missing Food. retry in {wait} minutes")
            self.checkFood()
            self.tasklist.addtask(wait+.2, f'Try Feeding {self.animal}', self.image, self.feed)
            return True
        return False

    def feed(self,atsite=False):
        try:
            self.log.debug('feeding')
            self.update()
            if not self.enabled:
                return False
            if not (atsite or self.locate_pen()):
                raise Exception("Could not locate pen")
            self.setWaittime(10)
            if atsite:
                self.execute(self.checkFed,self.icon_feed,steps=1)
                if self.checkMissingFood():
                    raise Exception("No Food available")
            if not self.checkFed():
                self.log.debug("Not all animals are fed.")
                self.execute(self.checkFed,self.icon_feed,steps=3)
                if self.checkMissingFood():
                    raise Exception("No Food available")
            self.checkFood()
            return True
        except Exception as e:
            self.log.error(self.name)
            self.log(e)
            return False

    def collect(self):
        try:
            self.log.debug(f'collecting: {self.product}')
            self.update()
            if not self.enabled:
                return False
            if not self.locate_pen():
                raise Exception(f"Could not locate {self.name}")
            if self.checkCollected():
                self.setWaittime(10)
                self.feed(True)
                raise Exception(f"Already Collected or not Fed")
            self.execute(self.checkCollected,self.icon_collect)
            self.setWaittime(5)
            if self.check_cross():
                raise Exception("Barn is full, need to sell something")
            self.tasklist.removeSchedule(self.product,self.amount)
            self.log.debug("Collection succesfull")
            self.setWaittime(10)
            if self.feed(True):
                self.setWaittime(self.eattime)
            self.scheduled=False
            self.checkJobs()
        except Exception as e:
            self.log.error(f"Fout in {self.name}")
            self.log.error(e)
            self.log.debug("retry in 5 minutes")
            self.tasklist.addtask(5, self.animal, self.image, self.collect)
        finally:
            self.exit()
