from hd import HD
from adb import Template
from glob import glob
from os import path
from time import(sleep)
from logger import MyLogger, logging


class Board(HD):
    def __init__(self, device, tasklist):
        HD.__init__(self, device, tasklist,'board')
        self.device=device
        self.tasklist=tasklist
        self.log=MyLogger('Board', LOG_LEVEL=logging.INFO)
        self.nextcheck=0.1
        self.image=path.join('images','board','car_button_C.png')
        self.base_template=HD.loadTemplates('board','base')
        self.complete_templates=HD.loadTemplates('board','check')
        # self.card_template=HD.loadTemplates('board','pins')
        self.product_templates={}
        self.car= [1335,775]
        self.bin= [1175,780]
        self.cards=[]
        for location in [[290,290],[535,290],[775,290],
                        [290,520],[535,520],[775,520],
                        [290,730],[535,730],[775,730]]:
            self.cards.append(Card(tasklist, location))
        self.product_images=[]
        self.checkImages()
        self.tasklist.addtask(self.nextcheck,'board',self.image,self.check)

    def checkImages(self):
        newimages=glob(path.join('images', 'products','*.png'))
        if newimages != self.product_images:
            self.log.debug('loading new templates')
            for file in newimages:
                filename=path.split(file)[-1]
                product=path.splitext(filename)[0]
                self.log.debug(f"found: {product}")
                self.product_templates[product]=Template(file)
        sleep(.5)
        self.product_images=newimages

    def getCard(self,location):
        list=[]
        for card in self.cards:
            list.append(card.location)
        location=self.device.getClosest(list, location)
        idx=list.index(location)
        return self.cards[idx]

    def collect(self, location):
        card=self.getCard(location)
        self.device.tap(*location)
        self.device.tap(*self.car)
        card.reset()

    def checkComplete(self):
        self.log.debug('checking complete')
        checks=self.device.locate_item(self.complete_templates,.85)
        if len(checks):
            self.collect(checks[0])
            self.nextcheck=.3
            return True
        return False

    def check(self):
        self.log.debug('checking board')
        self.checkImages()
        skiplist=HD.loadJSON('skip')
        self.nextcheck=1
        if self.reset_screen():
            location=self.device.locate_item(self.base_template,.75, one=True)
            self.log.debug(location)
            if len(location) and self.open(location):
                if not self.checkComplete():
                    self.log.debug('update board info')
                    for card in self.cards:
                        x,y=card.location
                        self.device.tap(x,y)
                        sleep(.1)
                        products=self.device.check_present(self.product_templates,.93)
                        for product in products:
                            if product in skiplist:
                                self.device.tap(*self.bin)
                                card.reset()
                                break
                            self.log.debug(f'found: {product}')
                            card.add(product)
                    self.nextcheck=5
                    self.checkComplete()
                self.check_cross()
        self.tasklist.addtask(self.nextcheck,'board',self.image,self.check)

class Card():
    def __init__(self,tasklist, location):
        self.tasklist=tasklist
        self.location = location
        self.requests = {}

    def add(self,product):
        if product not in self.requests:
            self.requests[product]=1
            self.tasklist.addWish(product)

        amount=self.requests[product]
        wishes,scheduled=self.tasklist.getWish(product)
        if (scheduled+wishes)<amount:
            self.tasklist.checkWish(product,amount)
            self.requests[product]+=1

    def reset(self):
        for product,amount in self.requests.items():
            self.tasklist.removeWish(product,amount)
        self.requests = {}

    def __repr__(self):
        return "Cards:"+", ".join(self.requests)
