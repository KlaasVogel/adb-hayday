from board import Board
from trees import Trees
from crops import Crops
from stations import Stations
from pens import Pens
from shop import Shop
from tasks import Tasklist
from adb import Adb_Device, ShowOutput
from tkinter import Tk, Frame
from gui import Buttons, Output, TaskListFrame, OrdersFrame, StationFrame
from threading import Thread

class MainApp(Tk):
    def __init__(self):
        self.root = Tk.__init__(self)
        self.device=Adb_Device()

        self.tl=Tasklist()
        self.buttons=Buttons(self, start=self.tl.start, pause= self.tl.hold, stop=self.tl.stop, capture=self.device.printScreen)
        self.buttons.grid(row=2,column=1)
        self.tasks=TaskListFrame(self, self.tl.getTaskList)
        self.tasks.grid(row=3, column=1)
        self.orders=OrdersFrame(self, self.tl.getWishList)
        self.orders.grid(row=3, column=2)

        self.stations=Stations(self.device, self.tl)
        self.stationFrame=StationFrame(self, self.stations.getList)
        self.stationFrame.grid(row=3, column=3)

        self.shop=Shop(self.device, self.tl)
        self.trees=Trees(self.device, self.tl)
        self.crops=Crops(self.device, self.tl)
        self.pens=Pens(self.device, self.tl)

        self.board=Board(self.device, self.tl)


        # self.output=Output(self)
        # self.output.grid(row=1, column=1)




        # self.shop.add('egg', min_amount=2, sell=True)
        # self.shop.add('milk', min_amount=2, sell=True)
        # self.shop.add('bacon', min_amount=2, sell=False)
        # self.shop.add('wool', min_amount=2, sell=False)
        # self.shop.add('wheat', min_amount=2, sell=False)
        # self.shop.add('corn', min_amount=2, sell=False)
        # self.shop.add('soy', min_amount=2, sell=False)
        # self.shop.add('carrot', min_amount=2, sell=False)
        # self.shop.add('sugarcane', min_amount=2, sell=False)
        # self.shop.add('pumpkin', min_amount=2, sell=False)
        # self.shop.add('indigo', min_amount=2, sell=False)
        # self.shop.add('cotton', min_amount=2, sell=False)
        # self.shop.add('bread', min_amount=2, sell=False)
        # self.shop.add('corn bread', min_amount=2, sell=False)
        # self.shop.add('cookie', min_amount=2, sell=False)


    def start(self):
        self.tl.start()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
