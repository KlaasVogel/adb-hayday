
from hd_objects import Board, Crops, Pens
from tasks import Tasklist
from adb import Adb_Device, ShowOutput
from tkinter import Tk, Frame
from gui import Buttons, Output
from threading import Thread



# test=Crop(device, 'test', tl, growtime=2 , threshold=.85 , field=0, icon_x=125, icon_y=160, pos_x=100 , pos_y=600)
#device.zoom_out()
# wheat=Crop(device, 'wheat', tl, growtime=2 , threshold=.85 , field=0, icon_x=125, icon_y=160, pos_x=100 , pos_y=600)
# carrot=Crop(device, 'carrot', tl, growtime=10 , threshold=.55 , field=0, icon_x=375, icon_y=10, pos_x=-75 , pos_y=300)
# corn=Crop(device, 'corn', tl , growtime=5 , threshold=.8 , field=1, icon_x=200, icon_y=25, pos_x=-400 , pos_y=550)
# soy=Crop(device, 'soy', tl, growtime=20 , threshold=.8 , field=0, icon_x=175, icon_y=300, pos_x=-250 , pos_y=700)
#
# mill1=Production(device, 'feed mill', tl, threshold=.4, icon_x=0, icon_y=-200, pos_x=-800, pos_y=-100)
# mill1.add(product='cow feed', worktime=10, icon_x=-200, icon_y=-200, second_menu=False)
# mill1.add(product='chicken feed', worktime=5, icon_x=0, icon_y=-250, second_menu=False)
# mill1.add(product='chicken feed', worktime=5, icon_x=0, icon_y=-250, second_menu=False)
# mill1.add(product='pig feed', worktime=20, icon_x=-300, icon_y=-125, second_menu=False)
# mill1.add(product='chicken feed', worktime=5, icon_x=0, icon_y=-250, second_menu=False)
# mill1.add(product='chicken feed', worktime=5, icon_x=0, icon_y=-250, second_menu=False)
# mill1.start()

# coop=Pen(device, tl, animal='chicken', product='egg', eattime=20, threshold=.7, size=300, icon_x=0, icon_y=-100, pos_x=-1000, pos_y=200)

# tl.start()

class MainApp(Tk):
    def __init__(self):
        self.root = Tk.__init__(self)
        self.tl=Tasklist()
        self.device=Adb_Device()
        self.crops=Crops(self.device, self.tl)
        self.pens=Pens(self.device, self.tl)
        self.board=Board(self.device, self.tl)
        self.buttons=Buttons(self, start=self.tl.start, pause= self.tl.hold, stop=self.tl.stop, capture=self.device.printScreen)
        self.output=Output(self)
        self.device.output.show=self.output.show.get
        self.output.grid(row=1, column=1)
        self.buttons.grid(row=2,column=1)
        self.crops.add('wheat', -10, 9)
        self.crops.add('carrot', -9, -3)
        self.pens.add('chicken', amount=6, lok_x=-13, lok_y=2)


    def start(self):
        self.tl.start()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
