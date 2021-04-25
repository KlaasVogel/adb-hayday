from time import time, sleep
from pynput import keyboard
from threading import Thread
import os

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

class Tasklist(dict):
    def __init__(self):
        self.busy=False
        self.running=False
        self.paused=False
        self.wishlist={}
    def addtask(self,waittime,name,image,job):
        print('adding job')
        new_time=int(time())+waittime*60
        while new_time in self:
            new_time+=1
        self[new_time]={'name':name,'image':image,'job':job}
    def printlist(self):
        cur_time=int(time())
        if not len(self):
            print('no jobs scheduled')
        for tasktime in sorted(self):
            remaining_time=tasktime-cur_time
            task=self[tasktime]
            print(f"JOB: {task['name']} in {remaining_time} seconds")
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
    def updateWish(self, name, amount):
        old=self.wishlist.get(name, 0)
        self.wishlist.update(name, old+amount)
    def checkWish(self, name):
        print(f"wishlist: {self.wishlist}")
        wish = self.wishlist.get(name, 0)
        if wish>0:
            return True
        return False


    def start(self):
        self.running=True
        self.thread=Thread(target=self.run, daemon=True).start()
    def hold(self):
        self.paused=not self.paused
    def stop(self):
        self.running=False
