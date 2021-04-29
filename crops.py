from hd import HD
from os import path
from math import isclose
from time import sleep, time
from glob import glob
from adb import Template

class Crops(list):
    device=None
    tasklist=None
    wheat=    {'growtime':  2, 'threshold':.85, 'field':0, 'set':1, 'icon':[366, -255]}
    corn=     {'growtime':  5, 'threshold':.90, 'field':1, 'set':1, 'icon':[238, -135]}
    carrot=   {'growtime': 10, 'threshold':.90, 'field':0, 'set':1, 'icon':[ 15, -125]}
    soy=      {'growtime': 20, 'threshold':.85, 'field':0, 'set':1, 'icon':[313, -410]}
    sugarcane={'growtime': 30, 'threshold':.85, 'field':1, 'set':1, 'icon':[130, -310]}
    indigo=   {'growtime':120, 'threshold':.75, 'field':0, 'set':2, 'icon':[366, -255]}
    pumpkin=  {'growtime':180, 'threshold':.90, 'field':1, 'set':2, 'icon':[238, -135]}

    templates={}
    empty_templates=[]
    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist
        self.empty_templates.append(HD.loadTemplates('crops','empty_0*'))
        self.empty_templates.append(HD.loadTemplates('crops','empty_1*'))
        self.switch_template=HD.loadTemplates('crops','switch*')
    def add(self, crop, amount=1, location=[0,0]):
        position = HD.getPos(location)
        if hasattr(self,crop):
            if crop not in self.templates:
                self.templates[crop]=HD.loadTemplates('crops',crop)
            data=getattr(self,crop)
            data['product']=crop
            data['temp_full']=self.templates[crop]
            data['temp_empty']=self.empty_templates[data['field']]
            data['temp_switch']=self.switch_template
            data['amount']=amount
            data['position']=position
            self.append(Crop(self.device, self.tasklist, data))

class Crop(HD):
    def __init__(self, device, tasklist, data):
        HD.__init__(self, device, tasklist,data['product'])
        for key,value in data.items():
            setattr(self, key, value)
        self.switch=[-485,120]
        self.scythe=[-190,-80]
        self.tasklist.addProduct(self.product, self.addJob, self.getJobTime)

    def getJobTime(self):
        waittime=self.getWaitTime()
        waittime+=self.jobs*self.growtime
        return waittime

    def addJob(self):
        self.jobs+=1
        self.checkJobs()
        return self.amount

    def checkJobs(self):
        print(f"checking jobs for {self.product}")
        wait = self.getWaitTime()
        if not self.scheduled:
            if self.jobs > 0 :
                print('adding task')
                self.jobs+=-1
                self.scheduled=True
                self.tasklist.addtask(wait/60+0.1, f'harvest {self.product}', self.image, self.harvest)
                return
            # self.tasklist.reset(self.product)

    def calcLocation(self,location):
        x,y=location
        dx,dy=self.switch
        x2=x-dx
        y2=y-dy
        return [x2,y2]

    def sow(self,fields):
        x,y=fields[0] if len(fields) else [800,450]
        print('sowing')
        empty_fields=self.device.locate_item(self.temp_empty, .9)
        waypoints=self.device.getClose(empty_fields, x,y,300,200)+fields
        if len(waypoints):
            x,y=waypoints[0]
            self.device.tap(x,y)
            sleep(.2)
            switch_location = self.device.locate_item(self.temp_switch, .85)
            if len(switch_location):
                x,y=switch_location[0]
                set_location=[x+90,y]
                (r,g,b)=self.device.getColor(set_location)
                print(f"colors ({x+90},{y}): {r},{g},{b}")
                set=1 if (r>200 and g>200 and b>150) else 2
                print(f"set: {set}    needs to be: {self.set}")
                if set != self.set:
                    self.device.tap(x,y)
                    sleep(.2)
                new_field_location=self.calcLocation(switch_location[0])
                self.device.correct(waypoints,[new_field_location])
                dx,dy=self.icon
                icon=[x+dx,y+dy]
                points=[icon]+waypoints
                self.device.trace(points)
                sleep(.2)
                self.check_cross()
            else:
                print('error!')
                wait=5 if self.growtime>5 else self.growtime
                self.setWaittime(wait)
                return
            self.setWaittime(self.growtime+0.5)

    def harvest(self):
        if self.reset_screen():
            self.move_to()
            print(f'harvesting: {self.product}')
            fields=self.device.locate_item(self.temp_full, threshold=self.threshold)
            if len(fields):
                dx,dy=self.scythe
                self.tap_and_trace(fields,dx,dy)
                if not self.check_cross():
                    self.tasklist.removeWish(self.product,self.amount)
                self.tasklist.removeSchedule(self.product,self.amount)
            sleep(2)
            self.sow(fields)
            self.scheduled=False
            self.checkJobs()
            self.move_from()
        else:
            self.tasklist.addtask(1,f'harvest {self.product}',self.image,self.harvest)
