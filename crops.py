from hd import HD, HomeException
from os import path
from math import isclose
from time import sleep, time
from glob import glob
from adb import Template
from logger import MyLogger, logging

class Crops(dict):
    switch_template=HD.loadTemplates('crops','switch*')
    def __init__(self, device, tasklist):
        self.log=MyLogger('Crops', LOG_LEVEL=logging.DEBUG)
        self.device=device
        self.tasklist=tasklist
        self.data=[]
        self.settings=[]
        self.updateListData()

    def updateListData(self):
        settings=HD.loadJSON('crops')
        resources=HD.loadJSON('resources')
        count={}
        if len(resources) and "crops" in resources and len(settings):
            if resources['crops']!=self.data or settings!=self.settings:
                self.data=resources['crops']
                self.settings=settings
                for crop in self.values():
                    crop.enabled=False
                for newcrop in self.data:
                    crop=newcrop['crop']
                    if crop not in count:
                        count[crop]=0
                    count[crop]+=1
                    name=f"Crop {crop} [{count[crop]}]"
                    if crop in self.settings:
                        if name not in self:
                            self[name]=Crop(self.device, self.tasklist, crop)
                        data=self.settings[crop]
                        data['log']=self.log
                        data['enabled']=True
                        data['position']=HD.getPos(newcrop['location'])
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
        self.filelist_full=[]
        self.filelist_empty=[]
        self.tasklist.addProduct(self.product, self.addJob, self.getJobTime)

    def checkTemplates(self):
        filelist_full=glob(path.join('images','crops',f"{self.product}*"))
        filelist_empty=glob(path.join('images','crops',f"empty_{self.field}*"))
        if filelist_full!=self.filelist_full:
            self.temp_full=HD.loadTemplates('crops',self.product)
            self.filelist_full=filelist_full
        if filelist_empty!=self.filelist_empty:
            self.filelist_empty=filelist_empty
            self.temp_empty=HD.loadTemplates('crops',f"empty_{self.field}*")

    def getJobTime(self):
        if not self.enabled:
            return False
        waittime=self.getWaitTime()+0.1
        waittime+=self.jobs*self.growtime
        return waittime

    def addJob(self):
        if not self.enabled:
            return 0
        self.jobs+=1
        self.checkJobs()
        return self.amount

    def checkJobs(self):
        self.log.info(f"checking jobs for {self.product}")
        self.update()
        wait = self.getWaitTime()+ 0.1
        if not self.scheduled and self.enabled:
            if self.jobs > 0 :
                self.log.info('adding task')
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
        try:
            self.checkTemplates()
            x,y=fields[0] if len(fields) else [800,450]
            self.log.info(f'sowing {self.product}')
            empty_fields=self.device.locate_item(self.temp_empty, .9)
            waypoints=self.device.getClose(empty_fields, x,y,300,200)+fields
            if not len(waypoints):
                raise Exception("Could not find empty fields")
            x,y=waypoints[0]
            self.device.tap(x,y)
            sleep(.2)
            switch_location = self.device.locate_item(self.temp_switch, .85)
            if not len(switch_location):
                raise Exception("Didn't Click on empty field")
            x,y=switch_location[0]
            set_location=[x+90,y]
            (r,g,b)=self.device.getColor(set_location)
            self.log.debug(f"colors ({x+90},{y}): {r},{g},{b}")
            set=1 if (r>100 and g>100 and b>100) else 2
            self.log.debug(f"set: {set}    needs to be: {self.set}")
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
            self.setWaittime(self.growtime+0.5)
        except Exception as e:
            self.log.error(f"fout in {self.product}")
            self.log.error(e)
            wait=5 if self.growtime>5 else self.growtime
            self.setWaittime(wait)

    def harvest(self):
        try:
            self.checkTemplates()
            if not self.reset_screen():
                raise HomeException("Could not find home")
            self.move_to()
            self.log.info(f'harvesting: {self.product}')
            fields=self.device.locate_item(self.temp_full, threshold=self.threshold)
            if not len(fields):
                raise Exception("Could not locate Crop")
            dx,dy=self.scythe
            self.tap_and_trace(fields,dx,dy)
            if self.check_cross():
                raise Exception("Silo is full")
            self.tasklist.removeSchedule(self.product,self.amount)
            self.sow(fields)
            self.scheduled=False
            self.checkJobs()
            wait=0
        except HomeException:
            self.log.error(e)
            wait=1
        except Exception as e:
            self.log.error(e)
            wait=5
        finally:
            if wait:
                self.tasklist.addtask(wait,f'harvest {self.product}',self.image,self.harvest)
            self.move_from()
