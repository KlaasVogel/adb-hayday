from hd import HD
from time import sleep
from os import path
from logger import MyLogger, logging

class Trees(dict):
    def __init__(self, device, tasklist):
        self.log=MyLogger('TREES', LOG_LEVEL=logging.INFO)
        self.device=device
        self.tasklist=tasklist
        self.data=[]
        self.settings=[]
        self.updateListData()

    def updateListData(self):
        self.log.debug('updating data')
        settings=HD.loadJSON('trees')
        resources=HD.loadJSON('resources')
        count={}
        if len(resources) and "trees" in resources and len(settings):
            self.log.debug('data is valid')
            if resources['trees']!=self.data or settings!=self.settings:
                self.data=resources['trees']
                self.settings=settings
                for fruit in self.values():
                    fruit.enabled=False
                for newfruit in self.data:
                    fruit=newfruit['fruit']
                    self.log.debug(f'fruit: {fruit}')
                    if fruit not in count:
                        count[fruit]=0
                    count[fruit]+=1
                    self.log.debug(f"amount: {newfruit['amount']}")
                    for i in range(newfruit['amount']):
                        name=f"{fruit} [{count[fruit]}-{i}]"
                        self.log.debug(f"name: {name}")
                        if fruit in self.settings:
                            if name not in self:
                                self[name]=Tree(self.device, self.tasklist, fruit)
                            data=self.settings[fruit].copy()
                            data['log']=self.log
                            data['name']=name
                            data['enabled']=True
                            data['position']=self.device.getPos(newfruit['location'])
                            data['templates']=HD.loadTemplateMap('trees',fruit)
                            data['update']=self.updateListData
                            for key,value in data.items():
                                setattr(self[name], key, value)

class Tree(HD):
    def __init__(self, device, tasklist, product):
        HD.__init__(self, device, tasklist, product)
        self.product=product
        self.enabled=True
        self.tasklist.addProduct(self.product, self.addJob, self.getJobTime)

    def harvest(self):
        print(f'harvesting {self.product}')
        self.update()
        if not self.enabled:
            return
        try:
            if not self.reset_screen():
                raise Exception("could not reset screen")
            self.move_to()
            self.tasklist.removeSchedule(self.product,self.times)
            tree=self.device.locate_item(self.templates, threshold=self.threshold, one=True)
            if not len(tree):
                # could not find tree, skip to next tree
                self.setWaittime(60)
                self.scheduled=False
                return
            self.device.center(tree)
            tree=self.device.locate_item(self.templates, threshold=self.threshold, one=True)
            x,y=tree
            dx,dy=self.icon
            self.device.tap(x,y)
            for i in range(self.times):
                self.device.swipe(x+dx,y+dy,x,y,400)
                sleep(.5)
            if not self.check_cross():
                self.tasklist.removeWish(self.product,self.times)
                wait=self.growtime+0.5
                self.setWaittime(wait)
                self.scheduled=False
                return
            self.setWaittime(5)
        except Exception as e:
            self.log.error("something went wrong....resetting")
            self.tasklist.addtask(5,f'{self.name} - harvest: {self.product}' ,self.image, self.harvest)
        finally:
            self.move_from()

    def getJobTime(self):
        if not self.enabled:
            return False
        waittime=self.getWaitTime()+0.05
        waittime+=self.jobs*self.growtime
        return waittime

    def addJob(self):
        if self.enabled:
            self.jobs+=1
            self.checkJobs()
            return self.times
        return 0

    def checkJobs(self):
        print(f"checking jobs for {self.product}")
        self.update()
        wait = self.getWaitTime()
        if not self.scheduled and self.enabled:
            if self.jobs > 0 :
                print('adding task')
                self.jobs+=-1
                self.scheduled=True
                self.tasklist.addtask(wait/60+0.1, f'{self.name} - harvest: {self.product}', self.image, self.harvest)
                return
            # self.tasklist.reset(self.product)
