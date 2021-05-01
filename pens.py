from hd import HD
from os import path
from math import isclose
from time import sleep, time
from glob import glob
from adb import Template
import numpy as np

class Pens(list):
    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist
        self.pen_templates={}
        self.collect_templates={}
        self.food_templates={}
        self.animal_data=HD.loadJSON('animals')

    def add(self, animal, amount=1, location=[0,0]):
        position = HD.getPos(location)
        if animal in self.animal_data:
            if animal not in self.pen_templates:
                self.pen_templates[animal]=HD.loadTemplates('pens',animal)
                self.collect_templates[animal]=HD.loadTemplates(path.join('pens','collect'),f'{animal}')
                self.food_templates[animal]=HD.loadTemplates(path.join('pens','food'),f'{animal}')
            data=self.animal_data[animal]
            product=data['product']
            data['temp_pen']=self.pen_templates[animal]
            data['temp_collect']=self.collect_templates[animal]
            data['temp_food']=self.food_templates[animal]
            data['position']=position
            data['amount']=amount
            self.append(Pen(self.device, self.tasklist, animal, product))
            self.setData(self[-1],data)

    @staticmethod
    def setData(pen, data):
        for key, value in data:
            setattr(pen, key, value)

    def update(self):
        self.animal_data=HD.loadJSON('animals')
        for pen in self:
            self.setData(pen, self.animal_data[pen.animal])

class Pen(HD):
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
            print('found')
            return False
        return True

    def checkFed(self):
        print(f"checking if all {self.animal} are fed")
        result=self.device.locate_item(self.temp_food, self.threshold_food)
        if len(result):
            print('found')
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
                return True
        return False

    def loadPath(self):
        data=self.loadJSON('paths')
        if not len(data):
            data={'default':[[0,0]]}
        trace_path=data[self.animal] if self.animal in data else data['default']
        return np.array(trace_path)

    def createWaypoints(self):
        trace_path=self.loadPath()
        waypoints = np.empty_like(trace_path)
        for i in range(trace_path.shape[0]):
          waypoints[i, :] = trace_path[i, :] + self.center
        return waypoints.tolist()

    def feed(self,atsite=False,waypoints=[]):
        print('feeding')
        print(atsite)
        if atsite or self.locate_pen():
            if not len(waypoints):
                waypoints=self.createWaypoints()
            dx,dy=self.icon_feed
            # print(waypoints)
            self.trace(waypoints, dx, dy)
            sleep(.3)
            if self.check_cross():
                print(f"Missing Food. retry in {self.wait} minutes")
                self.setWaittime(5)
                self.checkFood()
                self.tasklist.addtask(self.wait+.2, f'Try Feeding {self.animal}', self.image, self.feed)
                self.exit()
                return False
            if not self.checkFed():
                print("Not all animals are fed. Retry in 1 minute")
                self.setWaittime(1)
                self.tasklist.addtask(1.5, f"Feed: {self.animal}", self.image, self.feed)
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
        self.tasklist.addtask(1, self.animal, self.image, self.feed)
        return False

    def collect(self):
        print(f'collecting: {self.product}')
        if self.locate_pen():
            self.tasklist.removeSchedule(self.product,self.amount)
            if self.checkCollected():
                self.setWaittime(5)
                self.tasklist
                if not self.checkFed():
                    print("Not all animals are fed. Feeding and Resetting")
                    self.setWaittime(2)
                    self.feed(True)
                    return
                print("cannot collect, retry in 5 minutes")
                self.tasklist.addtask(5, f"Try to collect {self.product}", self.image, self.collect)
                self.exit()
                return
            dx,dy=self.icon_collect
            waypoints=self.createWaypoints()
            self.trace(waypoints, dx, dy)
            if self.check_cross():
                print("Barn is full, need to sell something")
                print("retry in 1 minute")
                self.tasklist.addtask(1, self.animal, self.image, self.collect)
                self.tasklist.sell_from_barn()
                self.exit()
                return
            if not self.checkCollected():
                print(f"Not all {self.product} collected")
                print("retry in 1 minute")
                self.tasklist.addtask(1, self.animal, self.image, self.collect)
                self.exit()
                return
            print("Collection succesfull")
            self.tasklist.removeWish(self.product,self.amount)
            self.feed(True,waypoints)
            return

        print('something went wrong')
        self.tasklist.addtask(1, self.animal, self.image, self.collect)
