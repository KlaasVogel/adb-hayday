from os import path
from math import isclose
from time import sleep
from glob import glob

class HD():
    def __init__(self,device,name,tasklist,threshold,pos_x,pos_y):
        self.device=device
        self.name=name
        self.tasklist=tasklist
        self.threshold=threshold
        file=path.join('images','products',f'{name}.png')
        self.image=file if path.isfile(file) else path.join('images','no_image.png')
        self.home=path.join('images','home.png')
        self.cross=path.join('images','X.png')
        self.pos_x=pos_x
        self.pos_y=pos_y
    def move_to(self):
        move(self.device, self.pos_x, self.pos_y)
        sleep(.2)
    def move_from(self):
        move(self.device, -self.pos_x, -self.pos_y)
    def check_full(self):
        locations=locate_item(self.device, self.cross,.45)
        if len(locations):
            x,y=locations[0]
            self.device.shell(f'input tap {x} {y}')
            sleep(1)
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
    def __init__(self, device, name, tasklist, threshold, icon_x, icon_y, pos_x=0, pos_y=0):
        HD.__init__(self, device, name, tasklist, threshold, pos_x, pos_y)
        self.template=path.join('images',name,'base.png')
        self.table=path.join('images','table.png')
        self.icon=[icon_x,icon_y]
        self.tasklist=tasklist
        self.worklist=[]
        self.job=0
    def add(self, product, worktime, icon_x, icon_y, second_menu=False):
        file=path.join('images','products',f'{product}.png')
        image=file if path.isfile(file) else path.join('images','no_image.png')
        self.worklist.append({"product":product,"image":image,"worktime":worktime,"icon":[icon_x,icon_y],"second_menu":second_menu})
    def start(self):
        if len(self.worklist):
            task=self.worklist[0]
            self.tasklist.addtask(2,task["product"],task["image"],self.produce)
    def produce(self):
        task=self.worklist[self.job]
        if self.reset_screen():
            self.move_to()
            location=locate_item(self.device, self.template, self.threshold, one=True)
            if len(location):
                x,y=location
                x=x+self.icon[0]
                y=y+self.icon[1]
                dx,dy=task['icon']
                self.device.shell(f"input tap {x} {y}")
                sleep(1)
                self.device.shell(f'input swipe {x+dx} {y+dy} {x} {y+100} 300')
                sleep(.5)
            self.move_from()
        self.job+=1
        if self.job==len(self.worklist):
            self.job=0
        nexttask=self.worklist[self.job]
        self.tasklist.addtask(task["worktime"],nexttask["product"],nexttask["image"],self.produce)

class Pen(HD):
    def __init__(self, device, tasklist, animal, product, eattime, threshold, size, icon_x, icon_y, pos_x=0, pos_y=0):
        HD.__init__(self, device, product, tasklist, threshold, pos_x, pos_y)
        self.animal=animal
        self.icon=[icon_x,icon_y]
        self.eattime=eattime
        self.size=size
        self.template=path.join('images','pens',f'{animal}-pen.png')
        self.full=path.join('images','pens',f'{animal}.png')
        self.tasklist.addtask(.02, self.animal, self.image, self.collect)
    def collect(self):
        if self.reset_screen():
            self.move_to()
            location=locate_item(self.device, self.template, self.threshold, one=True)
            if len(location):
                x,y=location
                self.device.shell(f'input tap {x+50} {y+50}')
                sleep(.2)
                dx2,dy2=self.icon
                dx1=dx2-105
                dy1=dy2+90
                animals=locate_item(self.device, self.full,.55)
                if animals:
                    self.swipe_animal(x+dx1,y+dy1,animals,dy=50)
                    sleep(2)
                    self.check_full()
                    self.swipe_animal(x+dx2,y+dy2,animals)
            self.move_from()
        self.tasklist.addtask(self.eattime, self.animal, self.image, self.collect)

    def swipe_animal(self,x,y,list,dx=0,dy=0):
        waypoints=[[x,y]]
        for location in list:
            x,y = location
            waypoints.append([x+dx, y+dy])
        trace(self.device,self.dev, waypoints, size=20, pressure=100)


class Crop(HD):
    def __init__(self, device, name, tasklist, growtime, threshold, icon_x, icon_y, field=0, second_menu=False, pos_x=0, pos_y=0):
        HD.__init__(self, device, name, tasklist, threshold, pos_x, pos_y)
        self.growtime=growtime
        self.icon=[icon_x,icon_y]
        self.fullcrop=path.join('images','crops',f'{name}.png')
        self.crop_selected=path.join('images','crops',f'{name}_select.png')
        self.field=path.join('images','crops',f'empty_{field}.png')
        self.field_selected=path.join('images','crops', f'empty_select_{field}.png')
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
            locations=locate_item(self.device, self.fullcrop, self.threshold)
            if len(locations):
                # self.tap_and_click(locations,130,30)
                # sleep(3)
                self.device.shell(f"input tap {locations[0][0]} {locations[0][1]}")
                sleep(.2)
                new=locate_item(self.device, self.crop_selected,0)
                if len(new):
                    locations=correct(locations,new)
                self.click(locations, 130,40)
                sleep(2)
                self.check_full()
            locations = locate_item(self.device, self.field,.9)
            if len(locations):
                self.device.shell(f"input tap {locations[0][0]} {locations[0][1]}")
                sleep(.2)
                new=locate_item(self.device, self.field_selected,0)
                if len(new):
                    locations=correct(locations,new)
                self.click(locations, *self.icon)
            self.move_from()
        self.tasklist.addtask(self.growtime,self.name,self.image,self.harvest)
