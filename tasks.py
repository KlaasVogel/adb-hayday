from time import time, sleep
from pynput import keyboard
from threading import Thread
from logger import MyLogger, logging
import os

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

class Wishlist(dict):
    def add(self, product, amount=1):
        if not product in self:
            self[product]={"amount":0, "scheduled":0}
        self[product]['amount']+=amount
    def get(self,product):
        if product in self:
            amount=self[product].get("amount",0)
            scheduled=self[product].get("scheduled",0)
            return [amount,scheduled]
        return [0,0]
    def check(self,product,amount):
        if product in self:
            wish,scheduled=self[product].values()
            if ((scheduled+wish)<amount):
                self[product]["amount"]=amount-scheduled
            return True
        self.add(product,amount)
    def reset(self,product,amount):
        if product in self:
            wish,scheduled=self[product].values()
            self[product]["amount"]=amount-scheduled if scheduled<amount else 0
            return
        self.add(product,amount)

class Tasklist(dict):
    def __init__(self):
        self.log=MyLogger('Tasklist', LOG_LEVEL=logging.INFO)
        self.busy=False
        self.running=False
        self.paused=False
        self.products={}
        self.wishlist=Wishlist()
        self.addWish=self.wishlist.add
        self.getWish=self.wishlist.get
        self.checkWish=self.wishlist.check
        self.resetWish=self.wishlist.reset


    def addtask(self,waittime,name,image,job):
        self.log.debug(f'\n adding job for {name}')
        new_time=int(time())+waittime*60
        while new_time in self:
            new_time+=1
        self[new_time]={'name':name,'image':image,'job':job}

    def addProduct(self, product, setjob, gettime):
        self.log.debug(f"adding product: {product}")
        if not product in self.products:
            self.products[product]=[]
        self.products[product].append({'setjob':setjob, 'gettime': gettime})

    def checkWishes(self):
        joblist=[]
        for product,data in self.wishlist.items():
            if data['amount']>0:
                joblist.append(product)
        for product in joblist:
            scheduled=self.setJob(product)
            self.wishlist[product]['scheduled']+=scheduled
            self.wishlist[product]['amount']-=scheduled

    def find(self, name):
        list=[]
        for task in self.values():
            if name in task['name']:
                list.append(task['name'])
        return list

    def getTaskList(self):
        data=[]
        if not len(self):
            data=['no jobs scheduled']
        for tasktime in sorted(self):
            remaining_time=tasktime-int(time())
            task=self[tasktime]
            data.append(f"{task['name']} in {self.printtime(remaining_time)}")
        return data

    def getWishList(self):
        list=dict(sorted(self.wishlist.items(), key=lambda item: item[0]))
        return list

    def setJob(self, product):
        try:
            self.log.debug(f'product: {product}')
            if product not in self.products:
                raise Exception("product is not listed")
            times=[]
            for station in self.products[product]:
                time=station['gettime']()
                if time:
                    times.append(station['gettime']())
            if not len(times):
                raise Exception("No Station found for this product")
            mintime=min(times)
            idx=times.index(mintime)
            return self.products[product][idx]['setjob']()
        except Exception as e:
            self.log.debug(e)
            return 0

    def reset(self,product):
        self.log.debug(f"resetting {product}:")
        self.wishlist.pop(product)

    def removeWish(self, product, amount):
        if product in self.wishlist:
            self.wishlist[product]['amount']-=amount

    def removeSchedule(self, product, amount):
        if product in self.wishlist:
            self.wishlist[product]['scheduled']-=amount
            if self.wishlist[product]['scheduled']<0:
                self.wishlist[product]['scheduled']=0
            if self.wishlist[product]['scheduled']==0 and self.wishlist[product]['amount']==0:
                self.wishlist.pop(product)

    def printlist(self):
        cur_time=int(time())
        if not len(self):
            self.log.debug('no jobs scheduled')
        for tasktime in sorted(self):
            remaining_time=tasktime-cur_time
            task=self[tasktime]
            self.log.debug(f"JOB: {task['name']} in {remaining_time} seconds")
        self.log.debug("\n")

        for product,data in self.wishlist.items():
            self.log.debug(f"WISH: {product} - {data}")

    def run(self):
        while self.running:
            # cls()
            cur_time=int(time())
            # if self.busy:
            #     self.log.debug(f"busy: {self.task['name']}")
            if not self.paused and len(self):
                firsttask=sorted(self)[0]
                if firsttask<=cur_time and not self.busy:
                    task=self.pop(firsttask)
                    self.busy=True
                    task['job']()
                    self.busy=False
            self.checkWishes()

    @staticmethod
    def printtime(seconds):
        if seconds <= 60:
            return f"{int(seconds)} seconds"
        if seconds <= 60*60:
            min=int(seconds/60)
            sec=int(seconds%60)
            return f"{min} minute(s) and {sec} seconds"
        hour=int(seconds/3600)
        min=int((seconds%3600)/60)
        sec=int(seconds%60)
        text=f"{hour} hour(s)"
        sep=", " if (min and sec) else " and "
        text=text+sep
        if min:
            text=text+f"{min} minute(s)"
        if sec:
            text=text+f" and {sec} seconds"
        return text

    def start(self):
        self.running=True
        self.thread=Thread(target=self.run, daemon=True).start()
    def hold(self):
        self.paused=not self.paused
    def stop(self):
        self.running=False
