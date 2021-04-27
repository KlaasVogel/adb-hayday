from os import path, getcwd
from math import isclose
from time import sleep, time
from glob import glob
from adb import Template

class HD():
    home=[Template(path.join('images','home_C.png'))]
    cross=[Template(path.join('images','X.png'))]
    def __init__(self,device,product,tasklist,threshold,pos_x,pos_y):
        self.device=device
        self.product=product
        self.tasklist=tasklist
        self.threshold=threshold
        file=path.join('images','products',f'{product}.png')
        self.image=file if path.isfile(file) else path.join('images','no_image.png')
        self.pos_x=pos_x
        self.pos_y=pos_y

    @staticmethod
    def loadTemplates(map, name):
        list=[]
        filelist=glob(path.join(getcwd(),'images', map ,f'{name}*.png'))
        for file in filelist:
            list.append(Template(file))
        return list

    @staticmethod
    def getPos(x,y):
        pos_x=40*x-40*y
        pos_y=-25*x-25*y-150
        return [pos_x, pos_y]

    def move_to(self):
        self.device.move(self.pos_x, self.pos_y)
        sleep(.2)
    def move_from(self):
        self.device.move(-self.pos_x, -self.pos_y)
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
    def check_home(self):
        locations=self.device.locate_item(self.home,.80)
        if not len(locations):
            print('ohoh')
            sleep(1)
            return False
        return locations
    def reset_screen(self):
        print('cleaning')
        locations=self.check_home()
        count=0
        while not locations or count>=3:
            if not self.check_full():
                for x in range(4):
                    self.device.swipe(200,150,1300,700,100)
                self.device.zoom_out()
                self.device.swipe(1300,300,600,400,400)
            locations=self.check_home()
            count+=1
        if not locations:
            return False
        x,y=locations[0]
        print(f'home: {x},{y}')
        if not (isclose(x,800,abs_tol=40) and isclose(y,350,abs_tol=40)):
            self.device.swipe(x,y,800,350,1000)
        sleep(.1)
        print('cleaning done')
        return True

    def tap_and_trace(self, locations, item_x=0, item_y=0):
        print('tap and trace')
        x,y=locations[0]
        self.device.tap(x,y)
        waypoints=[[x+item_x,y+item_y]]+locations
        print(waypoints)
        self.device.trace(waypoints)
        sleep(.5)

class Card():
    def __init__(self,tasklist, location):
        self.tasklist=tasklist
        self.location = location
        self.requests = {}
    def add(self,product):
        if product not in self.requests:
            self.requests[product] = {"scheduled":1}
            self.tasklist.updateWish(product)
        self.requests[product]["done"]=False
        status=self.requests[product]["scheduled"]-self.tasklist.getWish(product)
        print(f"status wish {product}: {status}")
    def reset(self):
        self.requests = {}
    def setdone(self):
        for request,data in self.requests.items():
            data["done"]=True
    def __repr__(self):
        products=[]
        for product,data in self.requests.items():
            text=f"{product} - done" if data["done"] else f"{product} - {data['scheduled']}"
            products.append(text)
        return "Cards:"+", ".join(products)

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
                    nextcheck=.5
                else:
                    print('update board info')
                    for card in self.cards:
                        card.setdone()
                        x,y=card.location
                        self.device.tap(x,y)
                        sleep(.1)
                        products=self.device.check_present(self.product_templates,.93)
                        for product in products:
                            print(f'found: {product}')
                            card.add(product)
                        nextcheck=5
                self.check_full()
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


class Pens(list):
    device=None
    tasklist=None
    chicken={'eattime':20, 'product':'egg', 'food':'chicken feed','threshold':.75,'icon_x':-120,'icon_y':-215}
    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist
        self.pen_templates={}
        self.full_templates={}
        self.empty_templates={}
    def add(self, animal, amount=1, threshold=None, lok_x=0, lok_y=0):
        pos_x, pos_y = HD.getPos(lok_x,lok_y)
        if hasattr(self,animal):
            if animal not in self.pen_templates:
                self.pen_templates[animal]=HD.loadTemplates('pens',animal)
                self.full_templates[animal]=HD.loadTemplates('animals',f'{animal}_full')
                self.empty_templates[animal]=HD.loadTemplates('animals',f'{animal}_empty')
            data=getattr(self,animal)
            self.append(Pen(self.device, self.tasklist, animal, amount,
                            data['food'], data['product'], data['eattime'], data['threshold'], data['icon_x'], data['icon_y'],
                            self.pen_templates[animal], self.full_templates[animal], self.empty_templates[animal], pos_x, pos_y))

class Pen(HD):
    def __init__(self, device, tasklist, animal, amount, food, product, eattime, threshold, icon_x, icon_y, temp_pen, temp_full, temp_empty, pos_x=0, pos_y=0):
        HD.__init__(self, device, product, tasklist, threshold, pos_x, pos_y)
        self.animal=animal
        self.amount=amount
        self.food=food
        self.icon_feed=[icon_x,icon_y]
        self.icon_collect=[icon_x-160,icon_y+140]
        self.eattime=eattime
        self.jobs=0
        self.temp_pen=temp_pen
        self.temp_full=temp_full
        self.temp_empty=temp_empty
        self.waiting=0
        self.tasklist.addProduct(product, self.addJob, self.getJobTime)
        # self.tasklist.addtask(.02, self.animal, self.image, self.collect)

    def getWaitTime(self):
        if self.waiting:
            waittime=self.waiting-int(time())
            if waittime > 0:
                return waittime
        return 0

    def setWaittime(self, wait):
        self.waiting=int(time()+wait*60)

    def getJobTime(self):
        waittime=self.getWaitTime()
        waittime+=self.jobs*self.eattime
        return waittime

    def addJob(self):
        self.jobs+=1
        self.tasklist.updateWish(self.food, self.amount)
        self.checkJobs()
        return self.amount

    def checkJobs(self):
        print(f"checking jobs for {self.product}")
        if not self.getWaitTime():
            print('adding task')
            self.tasklist.addtask(0.1, self.animal, self.image, self.collect)

    def feed(self,animals_full):
        print('feeding')
        x,y=animals_full[0]
        dx,dy=self.icon_feed
        animals= self.device.locate_item(self.temp_empty,.45, all=True)
        waypoints = animals_full + self.device.getClose(animals, x, y, 150, 75)
        print(waypoints)
        sleep(2)
        self.tap_and_trace(waypoints, dx, dy)
        sleep(2)
        if self.check_full():
            print('ohoh need feed')
            sleep(10)
        else:
            self.setWaittime(self.eattime)

    def collect(self):
        if self.reset_screen():
            self.move_to()
            location=self.device.locate_item(self.temp_pen, self.threshold, one=True)
            if len(location):
                x,y=location
                # print(f'tapping {self.animal}')
                # self.device.tap(x,y)
                # sleep(10)
                print('locating animals')
                animals=self.device.locate_item(self.temp_full,.50, all=True)
                waypoints=[location]+self.device.getClose(animals, x, y, 150,75)
                sleep(5)
                if animals:
                    dx,dy=self.icon_collect
                    self.tap_and_trace(waypoints, dx, dy)
                    if not self.check_full():
                        self.tasklist.removeWish(self.product,self.amount)
                self.feed(waypoints)
            sleep(10)
            self.move_from()
        # self.tasklist.addtask(self.eattime, self.animal, self.image, self.collect)


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
    def add(self, crop, amount=1, threshold=None, lok_x=0, lok_y=0):
        pos_x, pos_y = HD.getPos(lok_x,lok_y)
        if hasattr(self,crop):
            if crop not in self.templates:
                self.templates[crop]=HD.loadTemplates('crops',crop)
            data=getattr(self,crop)
            self.append(Crop(self.device, crop, amount, self.tasklist,
                             data['growtime'], data['threshold'], data['icon_x'], data['icon_y'], data['field'],
                             self.templates[crop], pos_x, pos_y))

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
        # self.tasklist.addtask(.1,self.name,self.image,self.harvest)

    def sow(self):
        print('sowing')
        empty_fields=self.device.locate_item(self.field_templates, .85)
        print(empty_fields)
        sleep(5)

    def harvest(self):
        if self.reset_screen():
            fields=self.device.locate_item(self.templates, threshold=self.threshold)
            if len(fields):
                self.tap_and_trace(fields,-130,-40)
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
