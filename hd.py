from os import path, getcwd
from math import isclose
from time import sleep, time
from glob import glob
from adb import Template
from logger import MyLogger
import json

class TemplateLibrary(dict):
    def __init__(self, filepath):
        filelist=glob(filepath)
        for file in filelist:
            filename=path.split(file)[-1]
            product=path.splitext(filename)[0]
            self[product]=Template(file)

class HD():
    # this needs to be placed inside of an update function to be able to change pictures while running
    home=None
    def __init__(self, device, tasklist, item):
        self.log=MyLogger('HD')
        self.device=device
        self.tasklist=tasklist
        self.scheduled=False
        file=path.join('images','products',f'{item}.png')
        self.image=file if path.isfile(file) else path.join('images','no_image.png')
        self.jobs=0
        self.waiting=0
        self.loadImages()
        print(self.home)

    def loadImages(self):
        for name in ['home', 'cross', 'info', 'plus', 'grass', 'diamond', 'again', 'arrows', 'cont']:
            setattr(self,name,self.loadTemplates('base',name))

    @staticmethod
    def loadJSON(filename):
        file=path.join('data',f'{filename}.json')
        try:
            if path.isfile(file):
                with open(file) as json_file:
                    data = json.load(json_file)
        except Exception as e:
            print(f"ERROR {filename}")
            print(e)
            data=[]
            sleep(5)
        finally:
            return data

    @staticmethod
    def loadTemplates(map, name):
        list=[]
        filelist=glob(path.join(getcwd(),'images', map ,f'{name}*.png'))
        for file in filelist:
            list.append(Template(file))
        return list

    @staticmethod
    def setData(item, data):
        for key, value in data.items():
            setattr(item, key, value)

    @staticmethod
    def getPos(location):
        x,y=location
        pos_x=40*x-40*y
        pos_y=-20*x-20*y
        return [pos_x, pos_y]

    #return time in minutes
    def getWaitTime(self):
        if self.waiting:
            waittime=self.waiting-int(time())
            if waittime > 0:
                return waittime/60
        return 0

    def setWaittime(self, wait):
        self.waiting=int(time()+wait*60)

    def move_to(self):
        pos_x,pos_y=self.position
        self.device.move(pos_x, pos_y)
        sleep(.2)
    def move_from(self):
        pos_x,pos_y=self.position
        self.device.move(-pos_x, -pos_y)
    def onscreen(self, product):
        self.log.debug(f"checking for {product}")
        templates=TemplateLibrary(path.join('images','products','big','*.png'))
        if product in templates:
            self.log.debug(f"Template is found")
            if len(self.device.locate_item([templates[product]],last=True)):
                return True
        return False
    def check_cross(self):
        locations=self.device.locate_item(self.cross,.45)
        if len(locations):
            x,y=locations[0]
            self.device.tap(x,y)
            return True
        return False
    def check_connection(self):
        locations=self.device.locate_item(self.again,.60)
        if len(locations):
            x,y=locations[0]
            self.device.tap(x,y)
            sleep(1)
    def check_lvl_up(self):
        locations=self.device.locate_item(self.cont,.75)
        if len(locations):
            x,y=locations[0]
            self.device.tap(x,y)
            sleep(1)
    def check_plus(self):
        locations=self.device.locate_item(self.plus,.85)
        if len(locations):
            return True
        return False
    def check_diamond(self):
        locations=self.device.locate_item(self.diamond,.85)
        if len(locations):
            return True
        return False
    def check_moved(self):
        locations=self.device.locate_item(self.arrows,.85)
        if len(locations):
            sleep(.3)
            self.click_green()
    def click_green(self):
        self.log.debug('click on grass')
        location=self.device.locate_item(self.grass,.45,one=True)
        if len(location):
            x,y=location
            self.device.tap(x,y)
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
    def check_home(self):
        locations=self.device.locate_item(self.home,.85)
        if not len(locations):
            self.log.debug('ohoh')
            return False
        return locations
    def reset_screen(self):
        self.log.debug('cleaning')
        locations=self.check_home()
        count=0
        while not locations or count>=3:
            self.check_connection()
            self.check_moved()
            self.check_lvl_up()
            if not self.check_cross():
                for x in range(4):
                    self.device.swipe(1300,150,200,700,100)
                self.check_cross()
                self.device.zoom_out()
                self.check_cross()
                self.device.swipe(800,600,1000,450,400)
            locations=self.check_home()
            count+=1
            self.loadImages()
        if not locations:
            return False
        x,y=locations[0]
        self.log.debug(f'home: {x},{y}')
        if not (isclose(x,800,abs_tol=100) and isclose(y,550,abs_tol=75)):
            self.device.swipe(x,y,800,550,1000)
        sleep(.1)
        self.log.debug('cleaning done')
        return True

    def tap_and_trace(self, locations, item_x=0, item_y=0):
        self.log.debug('tap and trace')
        x,y=locations[0]
        self.device.tap(x,y)
        waypoints=[[x+item_x,y+item_y]]+locations
        self.device.trace(waypoints,size=50)
        sleep(.5)

    def trace(self, locations, item_x=0, item_y=0):
        self.log.debug('trace')
        x,y=locations[0]
        waypoints=[[x+item_x,y+item_y]]+locations
        self.device.trace(waypoints,size=150)
        sleep(.2)
