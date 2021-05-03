from tkinter.ttk import Style, Frame, LabelFrame, Button, Checkbutton
from tkinter import IntVar, StringVar, Text, Canvas, SUNKEN, Y, X, Label
from glob import glob
from os import path, getcwd
from PIL import ImageTk, Image

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
        # self.frame=Frame(self,width=550,height=400)
        # self.frame.pack(expand=None, fill=Y)
        self.getData=source
        self.parent.after(1000, self.update)
        self.orders={}

    def update(self):
        try:
            data=self.getData()
            self.clearDict(self.orders, data)
            z=0
            for name,values in data.items():
                if name not in self.orders:
                    self.orders[name]=Order(self,name)
                self.orders[name].setData(**values)
                x,y,z=self.getXY(z,5)
                self.orders[name].grid(row=y,column=x)
        except Exception as e:
            print(e)
        finally:
            self.parent.after(5000, self.update)

    @staticmethod
    def getXY(i,max):
        x=i%max+1
        y=int(i/max)+1
        i+=1
        return [x,y,i]

    @staticmethod
    def clearDict(orders,data):
        deletelist=[]
        for name in orders:
            if name not in data:
                deletelist.append(order)
        for order in deletelist:
            orders[order].destroy()
            orders.pop(order)

class Order(LabelFrame):
    def __init__(self, parent, name):
        LabelFrame.__init__(self, parent, text=name)
        self.height=100
        self.width=100
        self.amount=IntVar()
        self.scheduled=IntVar()
        self.canvas=Canvas(self, bg='#FFF8B8', height=self.height,width=self.width, relief=SUNKEN)
        self.canvas.pack()
        self.img=Picture(self.canvas, name, self.height, relief=None, borderwidth=0, highlightthickness=0)
        x=int((self.width-self.img.width)/2)
        y=int((self.height-self.img.height)/2)
        self.img.place(x=x,y=y)
        self.lblA=Label(self.canvas, textvariable=self.amount,bg='#FFF8B8', font=("Verdana", 16))
        self.lblS=Label(self.canvas, textvariable=self.scheduled,bg='#FFF8B8', font=("Verdana", 16))
        d=3
        y=self.height-d
        self.lblA.place(x=d,y=y,anchor='sw')
        self.lblS.place(x=self.width-d,y=y,anchor='se')

    def setData(self, amount=0, scheduled=0, **kwargs):
        color1="darkgreen" if amount<0 else "red"
        color2="blue" if scheduled>0 else "black"
        self.lblA.config(fg=color1)
        self.lblS.config(fg=color2)
        self.amount.set(abs(amount))
        self.scheduled.set(scheduled)

class Picture(Label):
    def __init__(self, parent, name, maxheight, **kwargs):
        images=glob(path.join(getcwd(),'images','products',f"{name}.png"))
        if not len(images):
            images=glob(path.join(getcwd(),'images','products','big',f"{name}.png"))
        file=images[0] if len(images) else path.join(getcwd(),'images','no_image.png')
        image = Image.open(file)
        height=image.height
        if height>maxheight+10:
            width = (image.width*maxheight) // image.height
            image=image.resize((width,maxheight))
        self.width=image.width
        self.height=image.height
        self.img=ImageTk.PhotoImage(image)
        Label.__init__(self,parent,image=self.img, **kwargs)


class TaskListFrame(LabelFrame):
    def __init__(self, parent, source):
        LabelFrame.__init__(self, parent, text="Tasklist")
        self.parent=parent
        self.getData=source
        self.text=Text(self)
        self.text.pack()
        self.parent.after(1000, self.update)

    def update(self):
        try:
            data=self.getData()
            self.text.delete("1.0","end")
            for line in data:
                self.text.insert("end",str(line)+"\n")
        except Exception as e:
            print(e)
        finally:
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
            tasks="\n".join(station['tasks'])
            queue=", ".join(station['queue'])
            self.rows[idx].name.set(station['name'])
            self.rows[idx].jobs.set(f"Jobs: {station['jobs']}")
            self.rows[idx].time.set(f"Total Time: {station['time']}")
            self.rows[idx].tasks.set(f"Tasks: {tasks}")
            self.rows[idx].queue.set(f"Queue: {queue}")
        self.parent.after(5000, self.update)

class StationLabel(list):
    def __init__(self, parent, i):
        self.name=StringVar()
        self.jobs=StringVar()
        self.time=StringVar()
        self.tasks=StringVar()
        self.queue=StringVar()
        self.extend([Label(parent, textvariable=self.name),
                    Label(parent, textvariable=self.jobs),
                    Label(parent, textvariable=self.time),
                    Label(parent, textvariable=self.tasks),
                    Label(parent, textvariable=self.queue)])
        self[0].grid(row=1+i*3, column=1)
        self[1].grid(row=1+i*3, column=2)
        self[2].grid(row=1+i*3, column=3)
        self[3].grid(row=2+i*3, column=1, columnspan=3)
        self[4].grid(row=3+i*3, column=1, columnspan=3)
