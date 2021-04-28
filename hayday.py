
from hd import Board
from crops import Crops
from stations import Stations
from pens import Pens
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
        self.crops=Crops(self.device, self.tl)
        self.pens=Pens(self.device, self.tl)
        self.stations=Stations(self.device, self.tl)
        self.board=Board(self.device, self.tl)
        self.buttons=Buttons(self, start=self.tl.start, pause= self.tl.hold, stop=self.tl.stop, capture=self.device.printScreen)
        self.output=Output(self)
        self.device.output.show=self.output.show.get
        self.output.grid(row=1, column=1)
        self.buttons.grid(row=2,column=1)
        self.crops.add('wheat', amount=3, lok_x=4, lok_y=-2)
        self.crops.add('corn', amount=6, lok_x=-3, lok_y=-3)
        self.crops.add('soy', amount=5, lok_x=-6, lok_y=-3)
        self.crops.add('sugar cane', amount=4, lok_x=0, lok_y=-3)
        self.crops.add('carrot', amount=3, lok_x=-9, lok_y=-3)
        self.pens.add('chicken', amount=6, lok_x=-13, lok_y=2)
        self.pens.add('chicken', amount=6, lok_x=5, lok_y=-6)
        self.pens.add('cow', amount=5, lok_x=-8, lok_y=3)
        self.pens.add('pig', amount=5, lok_x=-10, lok_y=-1)
        self.stations.add('feed_mill', lok_x=-3, lok_y=4)
        self.stations.add('feed_mill', lok_x=-8, lok_y=-8)
        self.stations.add('dairy', lok_x=-7, lok_y=8)
        self.stations.add('bakery', lok_x=3, lok_y=10)
        self.stations.add('bbq_grill', lok_x=2, lok_y=10)
        self.stations.add('sugar_mill', lok_x=-3, lok_y=14)
        self.stations.add('popcorn_pot', lok_x=-3, lok_y=10)

    def start(self):
        self.tl.start()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
