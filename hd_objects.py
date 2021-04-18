from os import path
from adb_functions import locate_item, move, get_dev, correct
from math import isclose
from time import sleep

class HD():
    def __init__(self,device,name,tasklist,rel_x,rel_y):
        self.device=device
        self.name=name
        self.dev=get_dev(device)
        self.tasklist=tasklist
        file=path.join('images','products',f'{name}.png')
        self.image=file if path.isfile(file) else path.join('images','no_image.png')
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
            for x in range(4):
                self.device.shell('input swipe 200 150 1300 700 100')
            move(self.device,2900,1000)
            locations=locate_item(self.device, self.home,.9)
            if not len(locations):
                return False
        x,y=locations[0]
        if not (isclose(x,800,abs_tol=50) and isclose(y,350,abs_tol=50)):
            self.device.shell(f'input swipe {x} {y} 800 350 1000')
        return True

class Production(HD):
    def __init__(self, device, name, tasklist, threshold, rel_x=0, rel_y=0):
        HD.__init__(self, device, name, tasklist, rel_x, rel_y)
        self.template=path.join('images',name,'base.png')
        self.tasklist=[]
        self.nextjob=0
    def add(self, product, worktime, icon_x, icon_y, second_menu=False):
        # broken
        pass
        # self.tasklist.append({'name':self.name,'image':self.image, 'worktime':worktime,'second_menu':second_menu,'position':[icon_x,icon_y]})


class Crop(HD):
    def __init__(self, device, name, tasklist, growtime, threshold, icon_x, icon_y, field=0, second_menu=False, rel_x=0, rel_y=0):
        HD.__init__(self, device, name, tasklist, rel_x, rel_y)
        self.growtime=growtime
        self.icon=[icon_x,icon_y]
        self.fullcrop=path.join('images',name,'full.png')
        file=path.join('images','products',f'{name}.png')
        self.image=file if path.isfile(file) else path.join('images','no_image.png')
        self.field=path.join('images',f'empty_{field}.png')
        self.selected=path.join('images',f'empty_select_{field}.png')
        self.threshold=threshold
        self.tasklist.addtask(.2,self.name,self.image,self.harvest)

    def tap_and_click(self, locations, item_x, item_y):
        print('tap and click')
        x,y=locations[0]
        self.device.shell(f'input tap {x} {y}')
        # print(f'tap {x} {y}')
        sleep(.2)
        self.click(locations, item_x, item_y)

    def click(self, locations, item_x, item_y):
        x,y=locations[0]
        eventlist=[# f"{self.dev} 3 57 0",f"{self.dev} 3 53 {int((x)*32767/1600)}",f"{self.dev} 3 54 {int((y)*32767/900)}",f"{self.dev} 0 2 0", f"{self.dev} 0 0 0",f"{self.dev} 3 57 -1",f"{self.dev} 0 2 0",f"{self.dev} 0 0 0",
        f"{self.dev} 3 57 0",f"{self.dev} 3 53 {int((x-item_x)*32767/1600)}",f"{self.dev} 3 54 {int((y-item_y)*32767/900)}",f"{self.dev} 0 2 0", f"{self.dev} 0 0 0"]
        for location in locations:
            X,Y=location
            x=int((X)*32767/1600)
            y=int((Y)*32767/900)
            # print(X,Y,x,y)
            eventlist.append(f"{self.dev} 3 57 0")
            eventlist.append(f"{self.dev} 3 53 {x}")
            eventlist.append(f"{self.dev} 3 54 {y}")
            eventlist.append(f"{self.dev} 0 2 0")
            eventlist.append(f"{self.dev} 0 0 0")
        eventlist.append(f"{self.dev} 3 57 -1")
        eventlist.append(f"{self.dev} 0 2 0")
        eventlist.append(f"{self.dev} 0 0 0")
        for event in eventlist:
            # print(event)
            self.device.shell(event)

    def harvest(self):
        if self.reset_screen():
            self.move_to()
            sleep(.2)
            locations=locate_item(self.device, self.fullcrop,self.threshold)
            if len(locations):
                self.tap_and_click(locations,200,70)
                sleep(5)
            locations = locate_item(self.device, self.field,.9)
            if len(locations):
                self.device.shell(f"input tap {locations[0][0]} {locations[0][1]}")
                sleep(1)
                new=locate_item(self.device, self.selected,.8)
                if len(new):
                    locations=correct(locations,new)
                self.click(locations, *self.icon)
            self.move_from()
        self.tasklist.addtask(self.growtime,self.name,self.image,self.harvest)
