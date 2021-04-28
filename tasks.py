from time import time, sleep
from pynput import keyboard
from threading import Thread
import os

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

class Wishlist(dict):
    def add(self, product, amount=1):
        if not product in self:
            self[product]={"amount":amount, "scheduled":0}
        else:
            self[product]["amount"]+=amount
    def getWish(self,product):
        if product in self:
            return self[product].get("amount",0)
        return 0
    def checkWish(self,product):
        if product in self:
            wish=self[product].get("amount",0)
            if wish>0:
                return True
        return False


class Tasklist(dict):
    def __init__(self):
        self.busy=False
        self.running=False
        self.paused=False
        self.products={}
        self.wishlist=Wishlist()
        self.updateWish=self.wishlist.add
        self.getWish=self.wishlist.getWish
        self.checkWish=self.wishlist.checkWish
    def addtask(self,waittime,name,image,job):
        print('adding job')
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
    def checkWishes(self):
        joblist=[]
        for product,data in self.wishlist.items():
            if data['scheduled']-data['amount']<0:
                joblist.append(product)
        for product in  joblist:
            self.wishlist[product]['scheduled']+=self.setJob(product)
    def removeWish(self, product, amount):
        if product in self.wishlist:
            self.wishlist[product]['amount']-=amount
            if self.wishlist[product]['amount']<=0:
                self.wishlist.pop(product)
    def removeSchedule(self, product, amount):
        if product in self.wishlist:
            self.wishlist[product]['scheduled']-=amount
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

    def start(self):
        self.running=True
        self.thread=Thread(target=self.run, daemon=True).start()
    def hold(self):
        self.paused=not self.paused
    def stop(self):
        self.running=False
