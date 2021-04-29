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
    chicken={'eattime':20, 'product':'egg', 'food':'chicken feed','threshold':.75,'icon_feed':[-120,-240],'icon_collect':[-270,-115],'size':0,'centre':[-2,45]}
    cow={'eattime':60, 'product':'milk', 'food':'cow feed','threshold':.75,'icon_feed':[-100,-240],'icon_collect':[-250,-115],'size':1,'centre':[38,50]}
    pig={'eattime':240, 'product':'bacon', 'food':'pig feed','threshold':.75,'icon_feed':[-115,-285],'icon_collect':[-265,-185],'size':1,'centre':[-80,25]}
    sheep={'eattime':360, 'product':'wool', 'food':'sheep feed','threshold':.75,'icon_feed':[-115,-285],'icon_collect':[-265,-185],'size':1,'centre':[-30,75]}
    trace_path=[[[0,0],[37,19],[74,0],[37,-19],[0,-38],[-37,-19],[-74,0],[-37,19],[0,38],[0,8],[15,0],[0,-8],[-15,0]],
                [[ 37, 57],[ 74, 38],[ 111, 19],[ 148,0],[ 111,-19],[ 74,-38],[ 37,-57],[0,-76],
                 [-37,-57],[-74,-38],[-111,-19],[-148,0],[-111, 19],[-74, 38],[-37, 57],[0, 76]  ]]

    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist
        self.pen_templates={}
        self.full_templates={}
        self.empty_templates={}
    def add(self, animal, amount=1, location=[0,0]):
        position = HD.getPos(location)
        if hasattr(self,animal):
            if animal not in self.pen_templates:
                self.pen_templates[animal]=HD.loadTemplates('pens',animal)
                self.full_templates[animal]=HD.loadTemplates(path.join('animals',animal),f'{animal}_full')
                self.empty_templates[animal]=HD.loadTemplates(path.join('animals',animal),f'{animal}_empty')
            data=getattr(self,animal)
            data['animal']=animal
            data['trace_path']=self.trace_path[0]+self.trace_path[1] if data['size'] else self.trace_path[0]
            data['temp_pen']=self.pen_templates[animal]
            data['temp_full']=self.full_templates[animal]
            data['temp_empty']=self.empty_templates[animal]
            data['position']=position
            data['amount']=amount
            self.append(Pen(self.device, self.tasklist, data))

class Pen(HD):
    def __init__(self, device, tasklist, data):
        HD.__init__(self, device, tasklist, data['product'])
        for key,value in data.items():
            setattr(self, key, value)
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

    def checkJobs(self):
        print(f"checking jobs for {self.product}")
        wait=self.getWaitTime()
        if not self.scheduled:
            if self.jobs>0 :
                print('adding task')
                self.jobs+=-1
                self.tasklist.checkWish(self.food, 3)
                self.tasklist.addtask(wait/60+0.2, f"collect: {self.product}", self.image, self.collect)
                self.scheduled=True
                return
            # self.tasklist.reset(self.product)

    def checkFood(self):
        self.tasklist.checkWish(self.food, self.amount)

    def feed(self,waypoints):
        print('feeding')
        dx,dy=self.icon_feed
        # x,y=animals_full[0]
        #
        # animals= self.device.locate_item(self.temp_empty,.45, offset=[3,3])
        # waypoints = animals_full + self.device.getClose(animals, x, y, *self.margin)
        self.tap_and_trace(waypoints, dx, dy)
        sleep(.3)
        if self.check_cross():
            self.setWaittime(4)
            self.checkFood()
            self.tasklist.addtask(4, self.animal, self.image, self.collect)
            return False
        self.setWaittime(self.eattime)
        return True

    def collect(self):
        if self.reset_screen():
            self.move_to()
            print(f'collecting: {self.product}')
            location=self.device.locate_item(self.temp_pen, self.threshold, one=True)
            if len(location):
                self.scheduled=False
                centre=np.add(location,self.centre)
                dx,dy=self.icon_collect
                points=np.array(self.trace_path)
                waypoints = np.empty_like(points)
                for i in range(len(self.trace_path)):
                  waypoints[i, :] = points[i, :] + centre
                self.tap_and_trace(waypoints.tolist(), dx, dy)
                if not self.check_cross():
                    self.tasklist.removeWish(self.product,self.amount)
                if self.feed(waypoints.tolist()):
                    self.checkJobs()
                self.move_from()
                return
            self.move_from()
        #something went wrong
        print('something went wrong')
        self.tasklist.addtask(1, self.animal, self.image, self.collect)


        #old (for referense)

        #
        #         x,y=location
        #         animals=self.device.locate_item(self.temp_full,.45, offset=[3,3])
        #         waypoints=[location]+self.device.getClose(animals, x, y, *self.margin)
        #         if animals:
        #             dx,dy=self.icon_collect
        #             self.tap_and_trace(waypoints, dx, dy)
        #             if not self.check_cross():
        #                 self.tasklist.removeWish(self.product,self.amount)
        #             self.tasklist.removeSchedule(self.product, self.amount)
        #         if self.feed(waypoints):
        #             self.checkJobs()
        #         self.move_from()
        #         return
        #     self.move_from()
        # #something went wrong
        # print('something went wrong')
        # self.tasklist.addtask(1, self.animal, self.image, self.collect)
