from hd import HD
from os import path
from math import isclose
from time import sleep, time
from glob import glob
from adb import Template

class Pens(list):
    device=None
    tasklist=None
    chicken={'eattime':20, 'product':'egg', 'food':'chicken feed','threshold':.75,'icon':[-120,-215],'margin':[150,75]}
    cow={'eattime':60, 'product':'milk', 'food':'cow feed','threshold':.75,'icon':[-100,-215],'margin':[250,75]}
    pig={'eattime':240, 'product':'bacon', 'food':'pig feed','threshold':.75,'icon':[-115,-285],'margin':[350,75]}
    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist
        self.pen_templates={}
        self.full_templates={}
        self.empty_templates={}
    def add(self, animal, amount=1, threshold=None, lok_x=0, lok_y=0):
        pos_x, pos_y = HD.getPos(lok_x,lok_y)
        if hasattr(self,animal):
            if animal not in self.pen_templates:
                self.pen_templates[animal]=HD.loadTemplates('pens',animal)
                self.full_templates[animal]=HD.loadTemplates(path.join('animals',animal),f'{animal}_full')
                self.empty_templates[animal]=HD.loadTemplates(path.join('animals',animal),f'{animal}_empty')
            data=getattr(self,animal)
            self.append(Pen(self.device, self.tasklist, animal, amount,
                            data['food'], data['product'], data['eattime'], data['threshold'], data['icon'], data['margin'],
                            self.pen_templates[animal], self.full_templates[animal], self.empty_templates[animal], pos_x, pos_y))

class Pen(HD):
    def __init__(self, device, tasklist, animal, amount, food, product, eattime, threshold, icon, margin, temp_pen, temp_full, temp_empty, pos_x=0, pos_y=0):
        HD.__init__(self, device, product, tasklist, threshold, pos_x, pos_y)
        self.animal=animal
        self.amount=amount
        self.food=food
        self.icon_feed=icon
        self.icon_collect=[icon[0]-160,icon[1]+140]
        self.margin=margin
        self.eattime=eattime
        self.temp_pen=temp_pen
        self.temp_full=temp_full
        self.temp_empty=temp_empty
        self.scheduled=False
        self.tasklist.addProduct(product, self.addJob, self.getJobTime)

    def getJobTime(self):
        waittime=self.getWaitTime()
        waittime+=self.jobs*self.eattime
        return waittime

    def addJob(self):
        self.jobs+=1
        self.checkFood()
        self.checkJobs()
        return self.amount

    def checkJobs(self):
        print(f"checking jobs for {self.product}")
        wait=self.getWaitTime()
        if self.jobs>0 and not self.scheduled:
            print('adding task')
            self.jobs+=-1
            self.tasklist.addtask(wait/60+0.2, self.animal, self.image, self.collect)
            self.scheduled=True

    def checkFood(self):
        self.tasklist.checkWish(self.food, self.amount)

    def feed(self,animals_full):
        print('feeding')
        x,y=animals_full[0]
        dx,dy=self.icon_feed
        animals= self.device.locate_item(self.temp_empty,.45, offset=[5,5])
        waypoints = animals_full + self.device.getClose(animals, x, y, *self.margin)
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
                x,y=location
                animals=self.device.locate_item(self.temp_full,.45, offset=[4,4])
                waypoints=[location]+self.device.getClose(animals, x, y, *self.margin)
                if animals:
                    dx,dy=self.icon_collect
                    self.tap_and_trace(waypoints, dx, dy)
                    if not self.check_cross():
                        self.tasklist.removeWish(self.product,self.amount)
                    self.tasklist.removeSchedule(self.product, self.amount)
                if self.feed(waypoints):
                    self.checkJobs()
                self.move_from()
                return
            self.move_from()
        #something went wrong
        print('something went wrong')
        self.tasklist.addtask(1, self.animal, self.image, self.collect)
