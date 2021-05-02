from hd import HD
from os import path
from math import isclose
from time import sleep, time
from glob import glob
from adb import Template

class Crops(dict):
    device=None
    tasklist=None
    switch_template=HD.loadTemplates('crops','switch*')
    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist
        self.data=[]
        self.settings=[]
        self.updateListData()

    def updateListData(self):
        settings=HD.loadJSON('crops')
        resources=HD.loadJSON('resources')
        if len(resources) and "crops" in resources and len(settings):
            if resources['crops']!=self.data or settings!=self.settings:
                self.data=resources['crops']
                self.settings=settings
                for crop in self.values():
                    crop.enabled=False
                for newcrop in self.data:
                    crop=newcrop['crop']
                    name=newcrop['name']
                    if crop in self.settings:
                        if name not in self:
                            self[name]=Crop(self.device, self.tasklist, crop)
                        data=self.settings[crop]
                        data['enabled']=True
                        data['position']=HD.getPos(newcrop['location'])
                        data['temp_full']=HD.loadTemplates('crops',crop)
                        data['temp_empty']=HD.loadTemplates('crops',f"empty_{data['field']}*")
                        data['temp_switch']=self.switch_template
                        data['amount']=newcrop['amount']
                        data['update']=self.updateListData
                        for key,value in data.items():
                            setattr(self[name], key, value)

class Crop(HD):
    def __init__(self, device, tasklist, crop):
        HD.__init__(self, device, tasklist, crop)
        self.product=crop
        self.switch=[-485,120]
        self.scythe=[-190,-80]
        self.enabled=True
        self.tasklist.addProduct(self.product, self.addJob, self.getJobTime)

    def getJobTime(self):
        waittime=self.getWaitTime()
        waittime+=self.jobs*self.growtime
        return waittime

    def addJob(self):
        if not self.enabled:
            return 0
        self.jobs+=1
        self.checkJobs()
        return self.amount

    def checkJobs(self):
        print(f"checking jobs for {self.product}")
        self.update()
        wait = self.getWaitTime()+ 0.1
        if not self.scheduled and self.enabled:
            if self.jobs > 0 :
                print('adding task')
                self.jobs+=-1
                self.scheduled=True
                self.setWaittime(wait)
                self.tasklist.addtask(wait, f'harvest {self.product}', self.image, self.harvest)
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
                set=1 if (r>100 and g>100 and b>100) else 2
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
            self.setWaittime(5) #set wait if error sowing
            self.sow(fields)
            self.scheduled=False
            self.checkJobs()
            self.move_from()
        else:
            print('something went wrong')
            self.tasklist.addtask(1,f'harvest {self.product}',self.image,self.harvest)
