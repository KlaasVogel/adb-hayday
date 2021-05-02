from hd import HD
from time import sleep

class Shop(HD):
    def __init__(self, device, tasklist):
        HD.__init__(self, device, tasklist, 'money')
        self.tasklist.addtask(20, f"checking for items to sell", self.image, self.checkItems)
        self.products=[]

    def add(self, product, min_amount=6,sell=False):
        self.products.append(ShopItem(product, min_amount))

    def checkItems(self):
        for product in self.products:
            available=self.tasklist.getWish(product.name)
            if available>=product.min_amount:
                if self.tasklist.wishlist[product.name]["scheduled"]==0:
                    self.tasklist.addtask(0.5, f'Start selling of {product.name}', self.image, product.sell)
            else:
                self.tasklist.addWish(product.name, product.min_amount-available)
        self.tasklist.addtask(10, f"checking for items to sell", self.image, self.checkItems)

class ShopItem():
    def __init__(self, name, min_amount):
        self.name=name
        self.min_amount=min_amount

    def sell(self):
        print('whhoooooot')
        sleep(10)
