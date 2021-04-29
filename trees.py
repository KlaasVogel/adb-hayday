from hd import HD
from time import sleep

class Trees(list):
    device=None
    tasklist=None
    apples={'growtime': 16*60, 'times':3, 'threshold':.85, 'icon':[-185, 0]}
    templates={}
    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist

    def add(self, product, amount=1, location=[0,0]):
        position = HD.getPos(location)
        if hasattr(self,product):
            if product not in self.templates:
                self.templates[product]=HD.loadTemplates('trees',product)
            data=getattr(self,product)
            data['product']=product
            data['templates']=self.templates[product]
            data['position']=position
            for i in range(amount):
                self.append(Tree(self.device, self.tasklist, data ))

class Tree(HD):
    def __init__(self, device, tasklist, data):
        HD.__init__(self, device, tasklist, data['product'])
        for key,value in data.items():
            setattr(self, key, value)
        self.tasklist.addProduct(self.product, self.addJob, self.getJobTime)

    def harvest(self):
        print(f'harvesting {self.product}')
        if self.reset_screen():
            wait=2
            self.move_to()
            tree=self.device.locate_item(self.templates, threshold=self.threshold, one=True)
            if len(tree):
                x,y=tree
                dx,dy=self.icon
                self.device.tap(x,y)
                for i in range(self.times):
                    self.device.swipe(x+dx,y+dy,x,y,400)
                    sleep(.5)
                if not self.check_cross():
                    self.tasklist.removeWish(self.product,self.times)
                    wait=self.growtime+0.5
                self.tasklist.removeSchedule(self.product,self.times)
                self.scheduled=False
                self.setWaittime(wait)
                return
        print("something went wrong....resetting")
        self.tasklist.addtask(1,f'harvest {self.product}' ,self.image, self.harvest)

    def getJobTime(self):
        waittime=self.getWaitTime()
        waittime+=self.jobs*self.growtime
        return waittime

    def addJob(self):
        self.jobs+=1
        self.checkJobs()
        return self.times

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
