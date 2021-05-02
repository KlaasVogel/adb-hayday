from time import time, sleep
from pynput import keyboard
from threading import Thread
import os

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

class Wishlist(dict):
    def add(self, product, amount=1):
        if not product in self:
            self[product]={"amount":0, "scheduled":0}
        wishes, scheduled=self[product].values()
        if wishes<0:
            self[product]["amount"]=0
        if (amount-scheduled)>0:
            self[product]["amount"]+=(amount-scheduled)
    def getWish(self,product):
        if product in self:
            amount=self[product].get("amount",0)
            scheduled=self[product].get("amount",0)
            return scheduled-amount
        return 0
    def checkWish(self,product,amount):
        if product in self:
            wish,scheduled=(self[product]['amount'],self[product]['scheduled'])
            if ((scheduled+wish)<amount):
                self[product]["amount"]=amount-scheduled
            return True
        self.add(product,amount)

class Tasklist(dict):
    def __init__(self):
        self.busy=False
        self.running=False
        self.paused=False
        self.products={}
        self.wishlist=Wishlist()
        self.addWish=self.wishlist.add
        self.getWish=self.wishlist.getWish
        self.checkWish=self.wishlist.checkWish

    def addtask(self,waittime,name,image,job):
        print(f'\n adding job for {name}')
        new_time=int(time())+waittime*60
        while new_time in self:
            new_time+=1
        self[new_time]={'name':name,'image':image,'job':job}
    def addProduct(self, product, setjob, gettime):
        if not product in self.products:
            self.products[product]=[]
        self.products[product].append({'setjob':setjob, 'gettime': gettime})
    def setJob(self, product):
        if product in self.products:
            times=[]
            for station in self.products[product]:
                times.append(station['gettime']())
            mintime=min(times)
            idx=times.index(mintime)
            return self.products[product][idx]['setjob']()
        return 0
    def reset(self,product):
        print(f"resetting {product}:")
        self.wishlist.pop(product)
    def checkWishes(self):
        joblist=[]
        for product,data in self.wishlist.items():
            if data['scheduled']-data['amount']<0:
                joblist.append(product)
        for product in joblist:
            self.wishlist[product]['scheduled']+=self.setJob(product)
    def removeWish(self, product, amount):
        if product in self.wishlist:
            self.wishlist[product]['amount']-=amount
    def removeSchedule(self, product, amount):
        if product in self.wishlist:
            self.wishlist[product]['scheduled']-=amount
            if self.wishlist[product]['scheduled']<0:
                self.wishlist[product]['scheduled']=0
    def printlist(self):
        cur_time=int(time())
        if not len(self):
            print('no jobs scheduled')
        for tasktime in sorted(self):
            remaining_time=tasktime-cur_time
            task=self[tasktime]
            print(f"JOB: {task['name']} in {remaining_time} seconds")
        print("\n")
        self.checkWishes()
        for product,data in self.wishlist.items():
            print(f"WISH: {product} - {data}")
    def run(self):
        while self.running:
            cls()
            cur_time=int(time())
            if self.busy:
                print(f"busy: {self.task['name']}")
            if not self.paused and len(self):
                firsttask=sorted(self)[0]
                if firsttask<=cur_time and not self.busy:
                    task=self.pop(firsttask)
                    self.busy=True
                    task['job']()
                    self.busy=False
            self.printlist()
            sleep(1)

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
        data=[]
        for product,details in self.wishlist.items():
            data.append(f"{product} - {details}")
        return sorted(data)

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
