
from hd import Board
from trees import Trees
from crops import Crops
from stations import Stations
from pens import Pens
from shop import Shop
from tasks import Tasklist
from adb import Adb_Device, ShowOutput
from tkinter import Tk, Frame
from gui import Buttons, Output
from threading import Thread

class MainApp(Tk):
    def __init__(self):
        self.root = Tk.__init__(self)
        self.tl=Tasklist()
        self.device=Adb_Device()
        self.shop=Shop(self.device, self.tl)
        self.trees=Trees(self.device, self.tl)
        self.crops=Crops(self.device, self.tl)
        self.pens=Pens(self.device, self.tl)
        self.stations=Stations(self.device, self.tl)
        self.board=Board(self.device, self.tl)
        self.buttons=Buttons(self, start=self.tl.start, pause= self.tl.hold, stop=self.tl.stop, capture=self.device.printScreen)
        self.output=Output(self)
        self.device.output.show=self.output.show.get
        self.output.grid(row=1, column=1)
        self.buttons.grid(row=2,column=1)
        self.shop.add('egg', min_amount=14, sell=True)
        self.shop.add('milk', min_amount=12, sell=True)
        self.shop.add('bacon', min_amount=5, sell=False)
        self.shop.add('wool', min_amount=5, sell=False)
        self.shop.add('wheat', min_amount=8, sell=False)
        self.shop.add('corn', min_amount=8, sell=False)
        self.shop.add('soy', min_amount=8, sell=False)
        self.shop.add('carrot', min_amount=8, sell=False)
        self.shop.add('sugarcane', min_amount=6, sell=False)
        self.shop.add('pumpkin', min_amount=6, sell=False)
        self.shop.add('indigo', min_amount=6, sell=False)
        self.shop.add('cotton', min_amount=3, sell=False)
        self.shop.add('bread', min_amount=3, sell=False)
        self.shop.add('corn bread', min_amount=2, sell=False)
        self.shop.add('cookie', min_amount=2, sell=False)

        self.trees.add('apples',    amount=2, location=[-13,-13])
        self.crops.add('wheat',     amount=4, location=[  0, -3])
        self.crops.add('corn',      amount=4, location=[ -3, -3])
        self.crops.add('soy',       amount=4, location=[ -6, -3])
        self.crops.add('sugarcane', amount=5, location=[  3, -1])
        self.crops.add('carrot',    amount=4, location=[ -9, -3])
        self.crops.add('indigo',    amount=4, location=[-11,  7])
        self.crops.add('pumpkin',   amount=6, location=[-14,  8])
        self.crops.add('cotton',    amount=4, location=[ 8,  -5])
        self.pens.add('chicken', amount=6, location=[-13,  2])
        self.pens.add('chicken', amount=6, location=[  5, -6])
        self.pens.add('cow',     amount=5, location=[ -8,  3])
        self.pens.add('cow',     amount=5, location=[ -2,-13])
        self.pens.add('pig',     amount=5, location=[-12, -5])
        self.pens.add('sheep',   amount=5, location=[  4, 4])
        self.stations.add('feed_mill',   location=[-3, 4])
        self.stations.add('feed_mill',   location=[-13, -13])
        self.stations.add('dairy',       location=[-7, 8])
        self.stations.add('bakery',      location=[3, 10])
        self.stations.add('bbq_grill',   location=[10, -2])
        self.stations.add('sugar_mill',  location=[-3, 14])
        self.stations.add('popcorn_pot', location=[-3, 10])
        self.stations.add('pie_oven',    location=[8, 3])

    def start(self):
        self.tl.start()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
