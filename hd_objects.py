from os import path
from adb_functions import locate_item, move
from math import isclose
from time import sleep

class HD():
    def __init__(self,device,rel_x,rel_y):
        self.device=device
        self.home=path.join('images','home.png')
        self.rel_x=rel_x
        self.rel_y=rel_y
    def move_to(self):
        move(self.device, self.rel_x, self.rel_y)
    def move_from(self):
        move(self.device, -self.rel_x, -self.rel_y)
    def reset_screen(self):
        print('cleaning')
        locations=locate_item(self.device, self.home,.9)
        if not len(locations):
            print('ohoh...no home?')
        else:
            x,y=locations[0]
            if not (isclose(x,800,abs_tol=25) and isclose(y,350,abs_tol=25)):
                self.device.shell(f'input swipe {x} {y} 800 350 1000')


class Crop(HD):
    def __init__(self, device,  name, growtime, threshold, icon_x, icon_y, field=0, second_menu=False, rel_x=0, rel_y=0):
        HD.__init__(self, device, rel_x, rel_y)
        self.growtime=growtime
        self.icon=[icon_x,icon_y]
        self.fullcrop=path.join('images',name,'full.png')
        self.field=path.join('images',f'empty_{field}.png')
        self.threshold=threshold

    def clicks(self, locations, item_x, item_y):
        dev="sendevent /dev/input/event5"
        x,y=locations[0]
        self.device.shell(f'input tap {x} {y}')
        # print(f'tap {x} {y}')
        # sleep(5)
        eventlist=[# f"{dev} 3 57 0",f"{dev} 3 53 {int((x)*32767/1600)}",f"{dev} 3 54 {int((y)*32767/900)}",f"{dev} 0 2 0", f"{dev} 0 0 0",f"{dev} 3 57 -1",f"{dev} 0 2 0",f"{dev} 0 0 0",
        f"{dev} 3 57 0",f"{dev} 3 53 {int((x-item_x)*32767/1600)}",f"{dev} 3 54 {int((y-item_y)*32767/900)}",f"{dev} 0 2 0", f"{dev} 0 0 0"]
        for location in locations:
            X,Y=location
            x=int((X)*32767/1600)
            y=int((Y)*32767/900)
            print(X,Y,x,y)
            eventlist.append(f"{dev} 3 57 0")
            eventlist.append(f"{dev} 3 53 {x}")
            eventlist.append(f"{dev} 3 54 {y}")
            eventlist.append(f"{dev} 0 2 0")
            eventlist.append(f"{dev} 0 0 0")
        eventlist.append(f"{dev} 3 57 -1")
        eventlist.append(f"{dev} 0 2 0")
        eventlist.append(f"{dev} 0 0 0")
        for event in eventlist:
            # print(event)
            self.device.shell(event)

    def harvest(self):
        self.reset_screen()
        self.move_to()
        sleep(1)
        locations=locate_item(self.device, self.fullcrop,self.threshold)
        if len(locations):
            self.clicks(locations,200,70)
        sleep(6)
        locations=locate_item(self.device, self.field,.9)
        if len(locations):
            self.clicks(locations,*self.icon)
        self.move_from()
