from hd import HD
from os import path
from math import isclose
from time import sleep, time
from glob import glob
from adb import Template
import numpy as np

class Pens(list):
    device=None
    tasklist=None
    chicken={'eattime':20, 'product':'egg', 'food':'chicken feed','threshold':.75,'threshold_collect':0.95,'icon_feed':[-120,-240],'icon_collect':[-270,-115],'size':0,'center_offset':[-2,36]}
    cow={'eattime':60, 'product':'milk', 'food':'cow feed','threshold':.75,'threshold_collect':0.95,'icon_feed':[-100,-240],'icon_collect':[-250,-115],'size':1,'center_offset':[8,35]}
    pig={'eattime':240, 'product':'bacon', 'food':'pig feed','threshold':.75,'threshold_collect':0.98,'icon_feed':[-115,-285],'icon_collect':[-265,-185],'size':1,'center_offset':[-80,25]}
    sheep={'eattime':360, 'product':'wool', 'food':'sheep feed','threshold':.75,'threshold_collect':0.9,'icon_feed':[-115,-285],'icon_collect':[-265,-185],'size':1,'center_offset':[-30,75]}
    trace_paths={'chicken':[[0,0],[0,-8],[-15,0],[8,14],[15,0],[47,27],[80,7],[66,7],[35,-12],[-42,-17],[-89,7],[-104,7],[-37,19],[-55,33],[0,38],[0,55]],
                 'pig':[[0,0],[0,-8],[-15,0],[0,8],[15,0],
                        [ 30, 15],[ 60,  0],[ 30,-15],[0,-30],
                        [-30,-15],[-60,  0],[-30, 15],[0, 30],
                        [ 30, 45],[ 60, 30],[ 90, 15],[ 120,  0],[ 90,-15],[ 60,-30],[ 30,-45],[0,-60],
                        [-30,-45],[-60,-30],[-90,-15],[-120,  0],[-90, 15],[-69, 30],[-30, 45],[0, 60]],
           'cow':[[0,0],[ 30, 15],[ 60,  0],[ 30,-15],[0,-30],
                        [-30,-15],[-60,  0],[-30, 15],[0, 30],
                        [ 30, 45],[ 60, 30],[ 90, 15],[ 120,  0],[ 90,-15],[ 60,-30],[ 30,-45],[0,-60],
                        [-30,-45],[-60,-30],[-90,-15],[-120,  0],[-90, 15],[-60, 30],[-30, 45],[0, 60],
                        [ 30, 75],[ 60, 60],[ 90, 45],[ 120, 30],[150, 15]],
               'sheep':[[0,0],[0,-8],[-15,0],[0,8],[15,0],
                       [ 30, 15],[ 60,  0],[ 30,-15],[0,-30],
                       [-30,-15],[-60,  0],[-30, 15],[0, 30],
                       [ 30, 45],[ 60, 30],[ 90, 15],[ 120,  0],[ 90,-15],[ 60,-30],[ 30,-45],[0,-60],
                       [-30,-45],[-60,-30],[-90,-15],[-120,  0],[-90, 15],[-69, 30],[-30, 45],[0, 60]] }

    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist
        self.pen_templates={}
        self.collect_templates={}
        self.food_templates={}
    def add(self, animal, amount=1, location=[0,0]):
        position = HD.getPos(location)
        if hasattr(self,animal):
            if animal not in self.pen_templates:
                self.pen_templates[animal]=HD.loadTemplates('pens',animal)
                self.collect_templates[animal]=HD.loadTemplates(path.join('pens','collect'),f'{animal}')
                self.food_templates[animal]=HD.loadTemplates(path.join('pens','food'),f'{animal}')
            data=getattr(self,animal)
            data['animal']=animal
            data['trace_path']=np.array(self.trace_paths.get(animal,[[0,0]]))
            data['temp_pen']=self.pen_templates[animal]
            data['temp_collect']=self.collect_templates[animal]
            data['temp_food']=self.food_templates[animal]
            data['position']=position
            data['amount']=amount
            self.append(Pen(self.device, self.tasklist, data))

class Pen(HD):
    def __init__(self, device, tasklist, data):
        HD.__init__(self, device, tasklist, data['product'])
        for key,value in data.items():
            setattr(self, key, value)
        self.center=[0,0]
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
        result=self.device.locate_item(self.temp_food, 0.9)
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

    def createWaypoints(self):
        waypoints = np.empty_like(self.trace_path)
        # print(self.center)
        for i in range(self.trace_path.shape[0]):
          waypoints[i, :] = self.trace_path[i, :] + self.center
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
                print("Missing Food. retry in 5 minutes")
                self.setWaittime(5)
                self.checkFood()
                self.tasklist.addtask(5.2, f'Try Feeding {self.animal}', self.image, self.feed)
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
            self.checkJobs()
            self.exit()
            return True
        print('something went wrong')
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
            self.scheduled=False
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

        #         self.checkJobs()
        #     self.move_from()
        #     return
        # self.move_from()
    #something went wrong
        print('something went wrong')
        self.tasklist.addtask(1, self.animal, self.image, self.collect)
