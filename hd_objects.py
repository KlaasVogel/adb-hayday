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
    def __init__(self,device,product,tasklist,threshold,pos_x,pos_y):
        self.device=device
        self.product=product
        self.tasklist=tasklist
        self.threshold=threshold
        file=path.join('images','products',f'{product}.png')
        self.image=file if path.isfile(file) else path.join('images','no_image.png')
        self.pos_x=pos_x
        self.pos_y=pos_y
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
    def getPos(x,y):
        pos_x=40*x-40*y
        pos_y=-25*x-25*y-150
        return [pos_x, pos_y]

    def getWaitTime(self):
        if self.waiting:
            waittime=self.waiting-int(time())
            if waittime > 0:
                return waittime
        return 0

    def setWaittime(self, wait):
        self.waiting=int(time()+wait*60)

    def move_to(self):
        self.device.move(self.pos_x, self.pos_y)
        sleep(.2)
    def move_from(self):
        self.device.move(-self.pos_x, -self.pos_y)
    def check_cross(self):
        locations=self.device.locate_item(self.cross,.45)
        if len(locations):
            x,y=locations[0]
            self.device.tap(x,y)
            sleep(1)
            return True
        return False
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
            if not self.check_cross():
                for x in range(4):
                    self.device.swipe(1300,150,200,700,100)
                self.check_cross()
                self.device.zoom_out()
                self.check_cross()
                self.device.swipe(800,450,1000,600,400)
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
                    nextcheck=.3
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
                self.check_cross()
        self.tasklist.addtask(nextcheck,'board',self.image,self.check)


class Recipe():
    def __init__(self, station, product, recipe):
        self.station=station
        self.product=product
        for key,value in recipe.items():
            setattr(self, key, value)
            station.tasklist.addProduct(product, self.addJob, station.getJobTime)

    def addJob(self):
        self.station.jobs.append(self.product)
        for ingredient,amount in self.ingredients.items():
            self.station.tasklist.updateWish(ingredient, amount)
        self.station.checkJobs()
        return self.amount

    def create(self):
        self.station.start(self.product, self.icon, self.cooktime)

    def start_collect(self):
        self.station.collect(self.product,self.amount)

class Station(HD):
    def __init__(self, device, tasklist, station, recipes, threshold, templates, pos_x, pos_y):
        HD.__init__(self, device, station, tasklist, threshold, pos_x, pos_y)
        self.recipes={}
        self.templates=templates
        self.jobs=[]
        self.scheduled=False
        for product,recipe in recipes.items():
            self.recipes[product]=Recipe(self,product,recipe)

    def getJobTime(self):
        waittime=self.getWaitTime()
        for product in self.jobs:
            waittime+=self.recipes[product].cooktime
        return waittime

    def checkJobs(self):
        print(f"checking jobs for {self.product}")
        if not self.getWaitTime() and len(self.jobs) and not self.scheduled:
            print('adding task')
            product=self.jobs.pop(0)
            self.tasklist.addtask(0.2, product, self.image, self.recipes[product].create)
            self.scheduled=True

    def collect(self,product,amount=1):
        if self.reset_screen():
            self.move_to()
            if self.check_plus():
                self.click_green()
            location=self.device.locate_item(self.templates, self.threshold, one=True)
            if len(location):
                x,y=location
                self.device.tap(x,y)
                sleep(.2)
                if not self.check_cross():
                    self.tasklist.removeWish(product,amount)
                    self.tasklist.removeSchedule(product,amount)
                else:
                    self.tasklist.addtask(5, product, self.image, self.recipes[product].start_collect)
            self.checkJobs()
            self.move_from()
        else:
            self.tasklist.addtask(1, product, self.image, self.recipes[product].start_collect)

    def start(self,product,icon,cooktime):
        if self.reset_screen():
            self.move_to()
            if self.check_diamond():
                self.click_green()
            location=self.device.locate_item(self.templates, self.threshold, one=True)
            if len(location):
                print(f'found: {self.product}')
                x,y=location
                dx,dy=icon
                self.device.tap(x,y)
                print(f"should be opened now")
                newlocation=self.device.locate_item(self.templates, self.threshold, one=True)
                x,y = newlocation if len(newlocation) else location
                self.device.swipe(x+dx,y+dy,x,y,300)
                self.scheduled=False
                sleep(.1)
                if self.check_cross(): #could not find ingredients, wait 2 minutes
                    print('not enough ingredients')
                    self.setWaittime(2)
                    self.recipes[product].addJob()
                    self.move_from()
                    return
                self.setWaittime(cooktime)
                self.tasklist.addtask(cooktime, self.product, self.image, self.recipes[product].start_collect)
                self.move_from()
                return
            self.move_from()
        #something went wrong, try again in one minute
        self.tasklist.addtask(1, self.product, self.image, self.recipes[product].create)

class Stations(list):
    device=None
    tasklist=None
    feed_mill={'threshold':.75,'recipes':{
        'chicken feed':{'amount':3, 'cooktime':5, 'icon': [-50,-300], 'ingredients': {'wheat': 2, 'corn':1}},
        'cow feed':{'amount':3, 'cooktime':10, 'icon': [-220,-230], 'ingredients': {'soy': 2, 'corn':1}},
        'pig feed':{'amount':3, 'cooktime':20, 'icon': [-350,-110], 'ingredients': {'carrot': 2, 'soy':1}},
        'sheep feed':{'amount':3, 'cooktime':40, 'icon': [-390,50], 'ingredients': {}}   }}
    dairy={'threshold':.75,'recipes':{
        'cream':{'amount':1, 'cooktime':20, 'icon': [-15,-250], 'ingredients': {'milk': 1}},
        'butter':{'amount':1, 'cooktime':30, 'icon': [-185,-175], 'ingredients': {'milk': 2}},
        'cheese':{'amount':1, 'cooktime':60, 'icon': [-325,-55], 'ingredients': {'milk': 3}},
        'cheese2':{'amount':1, 'cooktime':120, 'icon': [-365,90], 'ingredients': {}}   }}
    sugar_mill={'threshold':.75,'recipes':{
        'brown sugar':{'amount':1, 'cooktime':20, 'icon': [-110,-130], 'ingredients': {'sugarcane': 1}},
        'white sugar':{'amount':1, 'cooktime':40, 'icon': [-245, 0], 'ingredients': {'sugarcane': 2}}   }}
    popcorn_pot={'threshold':.75,'recipes':{
        'popcorn':{'amount':1, 'cooktime':30, 'icon': [-135,-155], 'ingredients': {'corn': 2}},
        'pop2':{'amount':1, 'cooktime':120, 'icon': [-270,-25], 'ingredients': {}}   }}
    bbq_grill={'threshold':.75,'recipes':{
        'pancake':{'amount':1, 'cooktime':30, 'icon': [-127,-230], 'ingredients': {'egg': 3, 'brown sugar':1}},
        'bacon and eggs':{'amount':1, 'cooktime':60, 'icon': [-285,-120], 'ingredients': {'egg': 4,'bacon':2}},
        'burger':{'amount':1, 'cooktime':120, 'icon': [-345, 25], 'ingredients': {}}   }}
    bakery={'threshold':.75,'recipes':{
        'bread':{'amount':1, 'cooktime':5, 'icon': [-70,-270], 'ingredients': {'wheat': 3}},
        'cake':{'amount':1, 'cooktime':30, 'icon': [-240,-210], 'ingredients': {'corn': 2, 'egg':2}},
        'cookie':{'amount':1, 'cooktime':60, 'icon': [-370,-85], 'ingredients': {'wheat': 2, 'egg':2, 'brown sugar':1}},
        'cupcake':{'amount':1, 'cooktime':120, 'icon': [-415, 65], 'ingredients': {}}   }}

    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist
        self.templates={}
    def add(self, station, threshold=None, lok_x=0, lok_y=0):
        pos_x, pos_y = HD.getPos(lok_x,lok_y)
        if hasattr(self,station):
            if station not in self.templates:
                self.templates[station]=HD.loadTemplates('stations',station)
            data=getattr(self,station)
            self.append(Station(self.device, self.tasklist, station, data['recipes'], data['threshold'], self.templates[station], pos_x, pos_y ))

class Pens(list):
    device=None
    tasklist=None
    chicken={'eattime':20, 'product':'egg', 'food':'chicken feed','threshold':.75,'icon':[-120,-215],'margin':[150,75]}
    cow={'eattime':60, 'product':'milk', 'food':'cow feed','threshold':.75,'icon':[-100,-215],'margin':[250,75]}
    pig={'eattime':240, 'product':'bacon', 'food':'pig feed','threshold':.75,'icon':[-115,-285],'margin':[350,75]}
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
                self.full_templates[animal]=HD.loadTemplates(path.join('animals',animal),f'{animal}_full')
                self.empty_templates[animal]=HD.loadTemplates(path.join('animals',animal),f'{animal}_empty')
            data=getattr(self,animal)
            self.append(Pen(self.device, self.tasklist, animal, amount,
                            data['food'], data['product'], data['eattime'], data['threshold'], data['icon'], data['margin'],
                            self.pen_templates[animal], self.full_templates[animal], self.empty_templates[animal], pos_x, pos_y))

class Pen(HD):
    def __init__(self, device, tasklist, animal, amount, food, product, eattime, threshold, icon, margin, temp_pen, temp_full, temp_empty, pos_x=0, pos_y=0):
        HD.__init__(self, device, product, tasklist, threshold, pos_x, pos_y)
        self.animal=animal
        self.amount=amount
        self.food=food
        self.icon_feed=icon
        self.icon_collect=[icon[0]-160,icon[1]+140]
        self.margin=margin
        self.eattime=eattime
        self.temp_pen=temp_pen
        self.temp_full=temp_full
        self.temp_empty=temp_empty
        self.scheduled=False
        self.tasklist.addProduct(product, self.addJob, self.getJobTime)

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
        if not self.getWaitTime() and not self.scheduled:
            print('adding task')
            self.jobs-=1
            self.tasklist.addtask(0.1, self.animal, self.image, self.collect)
            self.scheduled=True

    def feed(self,animals_full):
        print('feeding')
        x,y=animals_full[0]
        dx,dy=self.icon_feed
        animals= self.device.locate_item(self.temp_empty,.45, all=True)
        waypoints = animals_full + self.device.getClose(animals, x, y, *self.margin)
        self.tap_and_trace(waypoints, dx, dy)
        sleep(.3)
        if self.check_cross():
            self.setWaittime(4)
            self.tasklist.addtask(4, self.animal, self.image, self.collect)
        else:
            self.setWaittime(self.eattime)

    def collect(self):
        if self.reset_screen():
            self.move_to()
            location=self.device.locate_item(self.temp_pen, self.threshold, one=True)
            if len(location):
                self.scheduled=False
                x,y=location
                animals=self.device.locate_item(self.temp_full,.45, all=True)
                waypoints=[location]+self.device.getClose(animals, x, y, *self.margin)
                if animals:
                    dx,dy=self.icon_collect
                    self.tap_and_trace(waypoints, dx, dy)
                    if not self.check_cross():
                        self.tasklist.removeWish(self.product,self.amount)
                self.feed(waypoints)
                self.checkJobs()
                self.tasklist.removeSchedule(self.product, self.amount)
            self.move_from()
            return
        #something went wrong
        self.tasklist.addtask(1, self.animal, self.image, self.collect)


class Crops(list):
    device=None
    tasklist=None
    wheat={'growtime':2, 'threshold':.85, 'field':0, 'icon_x':366, 'icon_y':-255}
    corn={'growtime':5, 'threshold':.85, 'field':1, 'icon_x':238, 'icon_y':-135}
    soy={'growtime':20, 'threshold':.85, 'field':0, 'icon_x':313, 'icon_y':-410}
    sugarcane={'growtime':30, 'threshold':.85, 'field':0, 'icon_x':135, 'icon_y':-305}
    carrot={'growtime':10, 'threshold':.85, 'field':0, 'icon_x':15, 'icon_y':-125}

    templates={}
    empty_templates=[]
    def __init__(self, device, tasklist):
        self.device=device
        self.tasklist=tasklist
        self.empty_templates.append(HD.loadTemplates('crops','empty_0*'))
        self.empty_templates.append(HD.loadTemplates('crops','empty_1*'))
        self.switch_template=HD.loadTemplates('crops','switch*')
    def add(self, crop, amount=1, threshold=None, lok_x=0, lok_y=0):
        pos_x, pos_y = HD.getPos(lok_x,lok_y)
        if hasattr(self,crop):
            if crop not in self.templates:
                self.templates[crop]=HD.loadTemplates('crops',crop)
            data=getattr(self,crop)
            self.append(Crop(self.device, crop, amount, self.tasklist,
                             data['growtime'], data['threshold'], data['icon_x'], data['icon_y'],
                             self.templates[crop],self.empty_templates[data['field']],self.switch_template,
                             pos_x, pos_y))

class Crop(HD):
    def __init__(self, device, product, amount, tasklist, growtime, threshold, icon_x, icon_y, temp_full, temp_empty, temp_switch, pos_x=0, pos_y=0):
        HD.__init__(self, device, product, tasklist, threshold, pos_x, pos_y)
        self.growtime=growtime
        self.amount=amount
        self.icon=[icon_x,icon_y]
        self.switch=[-485,120]
        self.scythe=[-190,-80]
        self.temp_full=temp_full
        self.temp_empty=temp_empty
        self.temp_switch=temp_switch
        self.tasklist.addProduct(product, self.addJob, self.getJobTime)

    def getJobTime(self):
        waittime=self.getWaitTime()
        waittime+=self.jobs*self.growtime
        return waittime

    def addJob(self):
        self.jobs+=1
        self.checkJobs()
        return self.amount

    def checkJobs(self):
        print(f"checking jobs for {self.product}")
        if not self.getWaitTime():
            print('adding task')
            self.jobs-=1
            self.tasklist.addtask(2, self.product, self.image, self.harvest)
        sleep(5)

    def calcLocation(self,location):
        x,y=location
        dx,dy=self.switch
        x2=x-dx
        y2=y-dy
        return [x2,y2]

    def sow(self,fields):
        print('sowing')
        empty_fields=self.device.locate_item(self.temp_empty, .9)
        # waypoints=fields+empty_fields
        if len(empty_fields):
            x,y=empty_fields[0]
            self.device.tap(x,y)
            sleep(.2)
            switch_location=self.device.locate_item(self.temp_switch, .85)
            if len(switch_location):
                x,y=switch_location[0]
                new_field_location=self.calcLocation(switch_location[0])
                self.device.correct(empty_fields,[new_field_location])
                dx,dy=self.icon
                icon=[x+dx,y+dy]
                waypoints=[icon]+empty_fields
                self.device.trace(waypoints)
                sleep(.2)
                self.check_cross()
            else:
                print('error!')
            self.setWaittime(self.growtime)


    def harvest(self):
        if self.reset_screen():
            self.move_to()
            print(f'harvesting: {self.product}')
            fields=self.device.locate_item(self.temp_full, threshold=self.threshold)
            if len(fields):
                dx,dy=self.scythe
                self.tap_and_trace(fields,dx,dy)
                if not self.check_cross():
                    self.tasklist.removeWish(self.product,self.amount)
                self.tasklist.removeSchedule(self.product,self.amount)
            self.sow(fields)
            self.checkJobs()
            self.move_from()
        else:
            self.tasklist.addtask(1,self.product,self.image,self.harvest)
