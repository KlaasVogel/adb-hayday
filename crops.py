from hd import HD, HomeException, Template
from os import path
from math import isclose
from time import sleep, time
from glob import glob
from adb import Template
from logger import MyLogger, logging

class Crops(dict):
    switch_template=HD.loadTemplates('crops','switch*')
    def __init__(self, device, tasklist):
        self.log=MyLogger('Crops', LOG_LEVEL=logging.INFO)
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
                self.log.error("Changes found")
                self.log.error(settings)
                self.log.error(self.settings)
                self.log.error(resources['crops'])
                self.log.error(self.data)
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
                        data=self.settings[crop].copy()
                        data.update(newcrop)
                        data['name']=name
                        data['log']=self.log
                        data['enabled']=True
                        self.log.debug(f"location: {newcrop['location']}")
                        data['position']=self.device.getPos(newcrop['location'])
                        self.log.debug(f"position: {data['position']}")
                        data['temp_switch']=self.switch_template
                        data['update']=self.updateListData
                        for key,value in data.items():
                            setattr(self[name], key, value)

class Crop(HD):
    def __init__(self, device, tasklist, crop):
        HD.__init__(self, device, tasklist, crop)
        self.switch=[-485,120]
        self.scythe=[-190,-80]
        self.enabled=True
        self.filelist_full=[]
        self.filelist_empt=[]
        self.filelist_trig=[]
        self.temp_full=[]
        self.temp_empt=[]
        self.temp_trig=[]
        self.tasklist.addProduct(crop, self.addJob, self.getJobTime)

    @staticmethod
    def checkMap(templates, filelist, newfilelist):
        if filelist!=newfilelist:
            templates=[]
            for file in newfilelist:
                templates.append(Template(file))
            filelist=newfilelist
        return templates

    def checkTemplates(self):
        filelist_full=glob(path.join('images','crops',f"{self.crop}",f"*.png"))
        self.temp_full=self.checkMap(self.temp_full, self.filelist_full, filelist_full)

        filelist_empt=glob(path.join('images','crops','empty',f"empty_{self.field}*"))
        self.temp_empt=self.checkMap(self.temp_empt, self.filelist_empt, filelist_empt)

        if hasattr(self, 'trigger') and hasattr(self, 'trig_vec'):
            filelist_trig=glob(path.join('images','crops','triggers',f"{self.trigger}*.png"))
            self.temp_trig=self.checkMap(self.temp_trig, self.filelist_trig, filelist_trig)

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
        self.log.debug(f"checking jobs for {self.crop}")
        self.update()
        wait = self.getWaitTime()+ 0.1
        if not self.scheduled and self.enabled:
            if self.jobs > 0 :
                self.log.debug('adding task')
                self.jobs+=-1
                self.scheduled=True
                self.setWaittime(wait)
                self.tasklist.addtask(wait, f'harvest {self.crop}', self.image, self.harvest)
                return
            # self.tasklist.reset(self.crop)

    def calcLocation(self,location):
        x,y=location
        dx,dy=self.switch
        x2=x-dx
        y2=y-dy
        return [x2,y2]

    def move_to_trigger(self):
        self.log.debug(f"{self.name} move to trigger")
        fields=[]
        try:
            location = self.device.locate_item(self.temp_trig, .75, one = True)
            self.log.debug(f"template: {self.temp_trig}  - location: {location}")
            if not len(location):
                raise Exception("Could not find trigger")
            self.device.center(*location)
            location = self.device.locate_item(self.temp_trig, .85, one = True)
            self.log.debug(f"location: {location}")
            for i in range(self.amount):
                fields.append(self.device.getPos(self.trig_vec,location,i+1))
        except Exception as e:
            self.log.error(self.name)
            self.log.error(e)
            quit()
        finally:
            self.log.debug(f"fields: {fields}")
            return fields

    def sow(self,fields):
        try:
            self.log.debug(f'sowing {self.crop}')
            self.checkTemplates()
            points=[]
            x,y=fields[0] if len(fields) else [self.device.scale_X(800),self.device.scale_Y(450)]
            if not len(fields) or not (hasattr(self,"trig_vec") and len(self.temp_trig)):
                self.log.debug(f"{self.crop} no fields and trigger")
                empty_fields=self.device.locate_item(self.temp_empt, .9)
                points=self.device.getClose(empty_fields, x,y,300,200)
                self.log.debug(f'points: {points}')
            waypoints=points+fields
            if not len(waypoints):
                raise Exception("Could not locate (empty) fields")
            x,y=waypoints[0]
            self.device.tap(x,y)
            sleep(.5)
            switch_location = self.device.locate_item(self.temp_switch, .85)
            if not len(switch_location):
                raise Exception("Didn't Click on empty field")
            x,y=switch_location[0]
            set_location=[x+90,y]
            (r,g,b)=self.device.getColor(set_location)
            self.log.debug(f"colors ({x+90},{y}): {r},{g},{b}")
            set=1 if (r>230 and g>230 and b>200) else 2
            self.log.debug(f"set: {set} needs to be: {self.set}")
            if set != self.set:
                self.device.tap(x,y)
                sleep(.2)
            self.log.debug(f"switch: {self.switch}")
            new_field_location=self.calcLocation(switch_location[0])
            self.log.debug(f"new field: {new_field_location}")
            self.device.correct(waypoints,[new_field_location])
            self.log.debug('')
            dx,dy=self.icon
            icon=[x+dx,y+dy]
            points=[icon]+waypoints
            self.device.trace(points)
            sleep(.2)
            self.check_cross()
            self.setWaittime(self.growtime+0.5)
        except Exception as e:
            self.log.error(f"fout in sowing {self.name}")
            self.log.error(e)
            wait=5 if self.growtime>5 else self.growtime
            self.setWaittime(wait)

    def harvest(self):
        fields=[]
        try:
            self.checkTemplates()
            if not self.reset_screen():
                raise HomeException("Could not find home")
            self.move_to()
            self.log.debug(f'harvesting: {self.crop}')
            if (hasattr(self,"trig_vec") and len(self.temp_trig)):
                fields=self.move_to_trigger()
            if not len(fields):
                self.log.debug(f"templates: {self.temp_full}")
                fields=self.device.locate_item(self.temp_full, threshold=self.threshold)
            if not len(fields):
                raise Exception("Could not locate Crop")
            dx,dy=self.scythe
            self.tap_and_trace(fields,dx,dy)
            sleep(2)
            if self.check_cross():
                raise Exception("Silo is full")
            self.tasklist.removeSchedule(self.crop,self.amount)
            self.sow(fields)
            self.scheduled=False
            self.checkJobs()
            wait=0
        except HomeException:
            self.log.error(e)
            wait=1
        except Exception as e:
            self.log.error(e)
            self.sow(fields)
            wait=5 if self.growtime>5 else self.growtime
        finally:
            if wait:
                self.tasklist.addtask(wait,f'harvest {self.crop}',self.image,self.harvest)
            self.move_from()
