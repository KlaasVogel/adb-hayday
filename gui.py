from tkinter.ttk import Style, Frame, LabelFrame, Label, Button, Checkbutton
from tkinter import IntVar, StringVar, Text

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


class OrdersFrame(LabelFrame):
    def __init__(self, parent, source):
        LabelFrame.__init__(self, parent, text="Orders")
        self.parent=parent
        self.getData=source
        self.text=Text(self)
        self.text.pack()
        self.parent.after(1000, self.update)

    def update(self):
        data=self.getData()
        self.text.delete("1.0","end")
        for line in data:
            self.text.insert("end",str(line)+"\n")
        self.parent.after(5000, self.update)


class TaskListFrame(LabelFrame):
    def __init__(self, parent, source):
        LabelFrame.__init__(self, parent, text="Tasklist")
        self.parent=parent
        self.getData=source
        self.text=Text(self)
        self.text.pack()
        self.parent.after(1000, self.update)

    def update(self):
        data=self.getData()
        self.text.delete("1.0","end")
        for line in data:
            self.text.insert("end",str(line)+"\n")
        self.parent.after(1000, self.update)


class StationFrame(LabelFrame):
    def __init__(self, parent, source):
        LabelFrame.__init__(self, parent, text="Stations")
        self.parent=parent
        self.getData=source
        self.rows=[]
        self.parent.after(1000, self.update)

    def update(self):
        data=self.getData()
        num_stations=len(data)
        num_rows=len(self.rows)
        if num_stations>num_rows:
            for i in range(num_rows,num_stations):
                self.rows.append(StationLabel(self,i))
        if num_rows>num_stations:
            for i in range(num_stations, num_rows):
                for label in self.rows[-1]:
                    label.destroy()
                self.rows.pop(-1)
        for idx,station in enumerate(data):
            self.rows[idx].name.set(station['name'])
            self.rows[idx].jobs.set(f"Jobs: {station['jobs']}")
            self.rows[idx].time.set(f"Total Time: {station['time']}")
            queue=", ".join(station['queue'])
            self.rows[idx].queue.set(f"Queue: {queue}")
        self.parent.after(5000, self.update)

class StationLabel(list):
    def __init__(self, parent, i):
        self.name=StringVar()
        self.jobs=StringVar()
        self.time=StringVar()
        self.queue=StringVar()
        self.extend([Label(parent, textvariable=self.name),
                    Label(parent, textvariable=self.jobs),
                    Label(parent, textvariable=self.time),
                    Label(parent, textvariable=self.queue)])
        self[0].grid(row=1+i*2, column=1)
        self[1].grid(row=1+i*2, column=2)
        self[2].grid(row=1+i*2, column=3)
        self[3].grid(row=2+i*2, column=1, columnspan=3)
