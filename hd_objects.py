from os import path, getcwd
from math import isclose
from time import sleep
from glob import glob
from adb import Template

class HD():
    home=[Template(path.join('images','home_C.png'))]
    cross=[Template(path.join('images','X.png'))]
    def __init__(self,device,name,tasklist,threshold,pos_x,pos_y):
        self.device=device
        self.name=name
        self.tasklist=tasklist
        self.threshold=threshold
        file=path.join('images','products',f'{name}.png')
        self.image=file if path.isfile(file) else path.join('images','no_image.png')
        self.pos_x=pos_x
        self.pos_y=pos_y
    def move_to(self):
        move(self.device, self.pos_x, self.pos_y)
        sleep(.2)
    def move_from(self):
        move(self.device, -self.pos_x, -self.pos_y)
    def check_full(self):
        locations=self.device.locate_item(self.cross,.45)
        if len(locations):
            x,y=locations[0]
            self.device.tap(x,y)
            sleep(1)
            return True
        return False
    def open(self, location):
        x,y=location
        self.device.tap(x,y)
        sleep(.1)
        if not self.check_open():
            self.device.tap(x,y)
            sleep(.1)
            if not self.check_open():
                self.tasklist.addtask(5,'board',self.image,self.check)
                return False
        return True
    def check_open(self):
        locations=self.device.locate_item(self.cross,.45)
        if len(locations):
            return True
        return False
    def reset_screen(self):
        print('cleaning')
        locations=self.device.locate_item(self.home,.9)
        if not len(locations):
            if not self.check_full():
                for x in range(4):
                    self.device.swipe(200,150,1300,700,100)
                self.device.zoom_out()
                self.device.swipe(1300,300,700,300,400)
            locations=self.device.locate_item(self.home,.9)
            if not len(locations):
                print('ohoh...no home?')
                return False
        x,y=locations[0]
        if not (isclose(x,800,abs_tol=40) and isclose(y,350,abs_tol=40)):
            self.device.swipe(x,y,800,350,1000)
        sleep(.1)
        return True


class Board(HD):
    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist
        self.image=path.join('images','board','car_button_C.png')
        self.base_template=[Template(path.join('images','board','base_TR_.png'))]
        self.complete_template=[Template(path.join('images','board','check_CR_.png'))]
        self.card_template=[Template(path.join('images','board','pins_C_B.png'))]
        self.icon=[1335,775]
        self.cards=[[290,290],[535,290],[775,290],
                    [290,520],[535,520],[775,520],
                    [290,730]]
        self.tasks=[]
        self.tasklist.addtask(.1,'board',self.image,self.check)

    def check(self):
        print('checking board')
        nextcheck=1
        if self.reset_screen():
            location=self.device.locate_item(self.base_template,.9, one=True)
            if len(location) and self.open(location):
                checks=self.device.locate_item(self.complete_template,.9)
                if len(checks):
                    x,y=checks[0]
                    self.device.tap(x,y)
                    sleep(.2)
                    x,y=self.icon
                    self.device.tap(x,y)
                    nextcheck=.2
                else:
                    print('update board info')


            nextcheck=5
        self.tasklist.addtask(nextcheck,'board',self.image,self.check)


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

class Crops(list):
    device=None
    tasklist=None
    wheat={'growtime':2, 'threshold':.85, 'field':0, 'icon_x':-125, 'icon_y':-150}
    corn={'growtime':5, 'threshold':.85, 'field':1, 'icon_x':3, 'icon_y':4}
    carrot={'growtime':10, 'threshold':.85, 'field':0, 'icon_x':3, 'icon_y':4}
    soy={'growtime':20, 'threshold':.85, 'field':0, 'icon_x':3, 'icon_y':4}
    templates={}
    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist
    def add(self, name, amount=1, threshold=None, pos_x=0, pos_y=0):
        if hasattr(self,name):
            self.loadTemplates(name)
            data=getattr(self,name)
            self.append(Crop(self.device, name, amount, self.tasklist, data['growtime'], data['threshold'], data['icon_x'], data['icon_x'], data['field'], self.templates[name], pos_x, pos_y))
    def loadTemplates(self, name):
        if name not in self.templates:
            list=[]
            filelist=glob(path.join(getcwd(),'images', 'crops',f'{name}*.png'))
            for file in filelist:
                list.append(Template(file))
                print(list[-1])
            self.templates[name]=list

class Crop(HD):
    fields=[]
    for i in range(2):
        list=[]
        glob_query=path.join('images', 'crops', f'empty_{i}*.png')
        glob_result=glob(glob_query)
        for file in glob_result:
            list.append(Template(file))
        fields.append(list)
    def __init__(self, device, name, amount, tasklist, growtime, threshold, icon_x, icon_y, field=0, templates=[], pos_x=0, pos_y=0):
        HD.__init__(self, device, name, tasklist, threshold, pos_x, pos_y)
        self.growtime=growtime
        self.amount=amount
        self.icon=[icon_x,icon_y]
        self.templates=templates
        self.field_templates=self.fields[field]
        self.scheduled=False
        # self.crop_selected=path.join('images','crops',f'{name}_select.png')
        # self.field=path.join('images','crops',f'empty_{field}.png')
        # self.field_selected=path.join('images','crops', f'empty_select_{field}.png')
        self.tasklist.addtask(.1,self.name,self.image,self.harvest)

    def tap_and_trace(self, locations, item_x=-130, item_y=-40):
        print('tap and trace')
        x,y=locations[0]
        self.device.tap(x,y)
        waypoints=[[x+item_x,y+item_y]]+locations
        print(waypoints)
        self.device.trace(waypoints)
        sleep(.5)

    def sow(self):
        print('sowing')
        empty_fields=self.device.locate_item(self.field_templates, .85)
        print(empty_fields)
        sleep(5)

    def harvest(self):
        if self.reset_screen():
            fields=self.device.locate_item(self.templates, threshold=self.threshold)
            if len(fields):
                self.tap_and_trace(fields)
                sleep(1)
                full = self.check_full()
                self.sow()
                self.tasklist.updateWish(self.name, -len(fields))
                if not full and self.tasklist.checkWish(self.name):
                    self.tasklist.addtask(self.growtime,self.name,self.image,self.harvest)
                    self.scheduled=True
                    return
            self.scheduled=False
        else:
            self.tasklist.addtask(1,self.name,self.image,self.harvest)
            self.scheduled=True

    #old function for reference, can be thrown away later
    def harvest_old(self):
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
