from os import path, getcwd
from math import isclose
from time import sleep, time
from glob import glob
from adb import Template

class HD():
    home=[Template(path.join('images','home_C.png'))]
    cross=[Template(path.join('images','X_C_.png'))]
    plus=[Template(path.join('images','plus_C_.png'))]
    grass=[Template(path.join('images','grass_C_.png'))]
    diamond=[Template(path.join('images','diamond_small.png'))]
    again=[Template(path.join('images','try_C_.png'))]
    arrows=[Template(path.join('images','arrows.png'))]
    cont=[Template(path.join('images','lvl_up_C_.png'))]

    def __init__(self, device, tasklist, item):
        self.device=device
        self.tasklist=tasklist
        self.scheduled=False
        file=path.join('images','products',f'{item}.png')
        self.image=file if path.isfile(file) else path.join('images','no_image.png')
        self.jobs=0
        self.waiting=0

    @staticmethod
    def loadTemplates(map, name):
        list=[]
        filelist=glob(path.join(getcwd(),'images', map ,f'{name}*.png'))
        for file in filelist:
            list.append(Template(file))
        return list

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
    def check_cross(self):
        locations=self.device.locate_item(self.cross,.45)
        if len(locations):
            x,y=locations[0]
            self.device.tap(x,y)
            sleep(1)
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
        print('click on grass')
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
            print('ohoh')
            return False
        return locations
    def reset_screen(self):
        print('cleaning')
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
        if not locations:
            return False
        x,y=locations[0]
        print(f'home: {x},{y}')
        if not (isclose(x,800,abs_tol=100) and isclose(y,550,abs_tol=75)):
            self.device.swipe(x,y,800,550,1000)
        sleep(.1)
        print('cleaning done')
        return True

    def tap_and_trace(self, locations, item_x=0, item_y=0):
        print('tap and trace')
        x,y=locations[0]
        self.device.tap(x,y)
        waypoints=[[x+item_x,y+item_y]]+locations
        self.device.trace(waypoints,size=50)
        sleep(.5)

    def trace(self, locations, item_x=0, item_y=0):
        print('trace')
        x,y=locations[0]
        waypoints=[[x+item_x,y+item_y]]+locations
        self.device.trace(waypoints,size=150)
        sleep(.2)

class Card():
    def __init__(self,tasklist, location):
        self.tasklist=tasklist
        self.location = location
        self.requests = []
    def add(self,product):
        if product not in self.requests:
            self.requests.append(product)
        self.tasklist.addWish(product)
    def reset(self):
        self.requests = []
    def __repr__(self):
        return "Cards:"+", ".join(self.requests)

class Board(HD):
    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist
        self.image=path.join('images','board','car_button_C.png')
        self.base_template=[Template(path.join('images','board','base_TR_.png'))]
        self.complete_template=[Template(path.join('images','board','check_CR_.png'))]
        self.card_template=[Template(path.join('images','board','pins_C_B.png'))]
        self.product_templates={}
        self.icon=[1335,775]
        self.cards=[]
        for location in [[290,290],[535,290],[775,290],
                        [290,520],[535,520],[775,520],
                        [290,730]]:
            self.cards.append(Card(tasklist, location))
        for file in glob(path.join('images', 'products','*.png')):
            filename=path.split(file)[-1]
            product=path.splitext(filename)[0]
            self.product_templates[product]=Template(file)
        self.tasklist.addtask(.1,'board',self.image,self.check)

    def getCard(self,location):
        list=[]
        for card in self.cards:
            list.append(card.location)
        location=self.device.getClosest(list, location)
        idx=list.index(location)
        return self.cards[idx]

    def collect(self, location):
        x,y = location
        card=self.getCard(location)
        print(card)
        self.device.tap(x,y)
        x,y=self.icon
        self.device.tap(x,y)
        card.reset()

    def check(self):
        print('checking board')
        nextcheck=1
        if self.reset_screen():
            location=self.device.locate_item(self.base_template,.75, one=True)
            if len(location) and self.open(location):
                checks=self.device.locate_item(self.complete_template,.9)
                if len(checks):
                    self.collect(checks[0])
                    nextcheck=.3
                else:
                    print('update board info')
                    for card in self.cards:
                        x,y=card.location
                        self.device.tap(x,y)
                        sleep(.1)
                        products=self.device.check_present(self.product_templates,.93)
                        for product in products:
                            print(f'found: {product}')
                            card.add(product)
                        nextcheck=5
                self.check_cross()
        self.tasklist.addtask(nextcheck,'board',self.image,self.check)
