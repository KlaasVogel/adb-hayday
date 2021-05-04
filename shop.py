from hd import HD
from time import sleep
from logger import MyLogger, logging

class Shop(HD):
    def __init__(self, device, tasklist):
        HD.__init__(self, device, tasklist, 'money')
        self.log=MyLogger('shop', LOG_LEVEL=logging.DEBUG)
        self.tasklist.addtask(20, f"checking for items to sell", self.image, self.checkItems)
        self.shoplist=Shoplist(self)
        self.position=HD.getPos([-15,0])
        self.slots=4
        self.max_slots=4
        self.atshop=False
        self.temp_shop=self.device.loadTemplates('shop','')

    def add(self, product, min_amount=6,sell=False):
        self.products.append(ShopItem(product, min_amount))

    def checkItems(self):
        self.atshop=False
        wait=10
        if self.max_slots>self.slots:
            self.checkShop()
            self.atshop=True
        try:
            json_data=HD.loadJSON('sell')
            for product,data in data.items():
                wished,scheduled=self.tasklist.getWish(product)

                #check if prodruct needs to be ordered
                if (scheduled-wished<data['maximum']-self.slots*data['amount']) and data['order']:
                    self.log.debug(f'need more {product}')
                    self.tasklist.addWish(product,data['maximum']-(scheduled-wished))

                if -wished>data['minimum']+data['amount']:
                    available=-wished-data['minimum']
                    stocks=int(available/data['amount'])
                    if stocks<self.slots:
                        self.slots-= stocks
                    else:
                        stocks=self.slots
                        self.slots=0
                    if stocks:
                        self.log.debug(f'i can sell some')
                        self.shoplist.add(product,stocks, **data)
                        wait=2
        except Exception as e:
            self.log.error(e)
        finally:
            self.tasklist.addtask(wait, f"checking for items to sell", self.image, self.checkItems)
            self.sellItems()

    def sellItems(self):
        self.log.debug('selling items')
        try:
            if not len(shoplist):
                raise Exception("No items to sell")
            if not self.atshop or self.open_shop():
                raise Exception("Shop is not open")
            spots=self.device.locate_item(self.temp_create, 0.85)
            for product,data in self.shoplist.items():
                if product in self.temp_products:
                    while self.shoplist[product].stock:
                        if not len(spots):
                            raise Exception("No free spot to sell items"):
                        location=spots.pop()
                        self.device.tap(location)
                        location=self.device.locate_item(self.temp_products[product],.85, one=True)
                        if not len(location):
                            raise Exception("Could not find product in list")
                        self.device.tap(location)
                        self.log.debug('item should be selected by now')





            if not len(locations):
                raise



        except Exception as e:
            self.log.error(e)

    def checkShop(self):
        self.log.debug('checking Shop')
        try:
            if not self.open_shop():
                raise Exception("Shop is not open")
            locations=self.device.locate_item(self.temp_sold, 0.85)
            if not len(locations):
                raise Exception("Could not find sold items")
            for location in locations:
                self.device.tap(location)
        except Exception as e:
            self.log.error(e)

    def open_shop(self):
        try:
            self.move_to()
            location = self.device.locate_item(self.temp_shop, .85, one = True)
            if not len(location):
                raise Exception("Could not locate shop")
            self.device.tap(location)
            self.atshop=True
            return True
        except Exception as e:
            self.log.error('OPEN SHOP')
            self.log.error(e)
            return False

class ShopList(dict):
    def __init__(self, shop):
        self.shop=shop

    def add(self, product, available, **kwargs):
        if product not in self:
            self[product]=Product(product, **kwargs)
            setattr(self[product],'stock',0)
        self[product].stock+=available

class Product():
    def __init__(self, product, **kwargs):
        self.__dict__.update(kwargs)
