from tkinter.ttk import Style, Frame, LabelFrame, Button, Checkbutton
from tkinter import IntVar

def doNothing():
    pass

class Buttons(Frame):
    def __init__(self,parent,start=doNothing, pause=doNothing, stop=doNothing, capture=doNothing):
        Frame.__init__(self,parent)
        self.master=parent
        self.btn_start=Button(self, text="start", command=start)
        self.btn_pause=Button(self, text="pause", command=pause)
        self.btn_stop=Button(self, text="stop", command=stop)
        self.btn_cap=Button(self, text="capture", command=capture)
        self.btn_start.pack(side='left')
        self.btn_pause.pack(side='left')
        self.btn_stop.pack(side='left')
        self.btn_cap.pack(side='bottom')

class Output(LabelFrame):
    def __init__(self, parent):
        LabelFrame.__init__(self, parent, text="Output")
        self.show=IntVar(value=False)
        self.cb=Checkbutton(self, text="show output", variable=self.show)
        self.cb.pack(side="left")
