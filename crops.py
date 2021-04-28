from hd import HD
from os import path
from math import isclose
from time import sleep, time
from glob import glob
from adb import Template

class Crops(list):
    device=None
    tasklist=None
    wheat={'growtime':2, 'threshold':.85, 'field':0, 'icon_x':366, 'icon_y':-255}
    corn={'growtime':5, 'threshold':.85, 'field':1, 'icon_x':238, 'icon_y':-135}
    soy={'growtime':20, 'threshold':.85, 'field':0, 'icon_x':313, 'icon_y':-410}
    sugarcane={'growtime':30, 'threshold':.85, 'field':0, 'icon_x':135, 'icon_y':-305}
    carrot={'growtime':10, 'threshold':.85, 'field':0, 'icon_x':15, 'icon_y':-125}

    templates={}
    empty_templates=[]
    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist
        self.empty_templates.append(HD.loadTemplates('crops','empty_0*'))
        self.empty_templates.append(HD.loadTemplates('crops','empty_1*'))
        self.switch_template=HD.loadTemplates('crops','switch*')
    def add(self, crop, amount=1, threshold=None, lok_x=0, lok_y=0):
        pos_x, pos_y = HD.getPos(lok_x,lok_y)
        if hasattr(self,crop):
            if crop not in self.templates:
                self.templates[crop]=HD.loadTemplates('crops',crop)
            data=getattr(self,crop)
            self.append(Crop(self.device, crop, amount, self.tasklist,
                             data['growtime'], data['threshold'], data['icon_x'], data['icon_y'],
                             self.templates[crop],self.empty_templates[data['field']],self.switch_template,
                             pos_x, pos_y))

class Crop(HD):
    def __init__(self, device, product, amount, tasklist, growtime, threshold, icon_x, icon_y, temp_full, temp_empty, temp_switch, pos_x=0, pos_y=0):
        HD.__init__(self, device, product, tasklist, threshold, pos_x, pos_y)
        self.growtime=growtime
        self.scheduled=False
        self.amount=amount
        self.icon=[icon_x,icon_y]
        self.switch=[-485,120]
        self.scythe=[-190,-80]
        self.temp_full=temp_full
        self.temp_empty=temp_empty
        self.temp_switch=temp_switch
        self.tasklist.addProduct(product, self.addJob, self.getJobTime)

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
        if self.jobs>0 and not self.scheduled:
            print('adding task')
            self.jobs+=-1
            self.scheduled=True
            self.tasklist.addtask(wait/60+0.3, self.product, self.image, self.harvest)

    def calcLocation(self,location):
        x,y=location
        dx,dy=self.switch
        x2=x-dx
        y2=y-dy
        return [x2,y2]

    def sow(self,fields):
        print('sowing')
        empty_fields=self.device.locate_item(self.temp_empty, .9)
        # waypoints=fields+empty_fields
        if len(empty_fields):
            x,y=empty_fields[0]
            self.device.tap(x,y)
            sleep(.2)
            switch_location=self.device.locate_item(self.temp_switch, .85)
            if len(switch_location):
                x,y=switch_location[0]
                new_field_location=self.calcLocation(switch_location[0])
                self.device.correct(empty_fields,[new_field_location])
                dx,dy=self.icon
                icon=[x+dx,y+dy]
                waypoints=[icon]+empty_fields
                self.device.trace(waypoints)
                sleep(.2)
                self.check_cross()
            else:
                print('error!')
            self.setWaittime(self.growtime)

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
            self.tasklist.addtask(1,self.product,self.image,self.harvest)
