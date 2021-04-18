from ppadb.client import Client
from hd_objects import Crop
from time import time, sleep
from pynput import keyboard
import os

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

break_program = False
paused=False
def on_press(key):
    global break_program
    global paused
    print (key)
    key
    if key == keyboard.Key.end or key.char == 'q':
        print ('end pressed')
        break_program = True
        return False
    if key.char == 'p':
        print('pause?')
        paused=False if paused else True


class Tasklist(dict):
    def __init__(self):
        self.busy=False
        self.running=False
        self.timer=None
    def addtask(self,waittime,name,image,job):
        print('adding job')
        new_time=int(time())+waittime*60
        while new_time in self:
            new_time+=1
        self[new_time]={'name':name,'image':image,'job':job}
    def printlist(self):
        cur_time=int(time())
        for tasktime in sorted(self):
            remaining_time=tasktime-cur_time
            task=self[tasktime]
            print(f"JOB: {task['name']} in {remaining_time} seconds")
    def start(self):
        with keyboard.Listener(on_press=on_press) as listener:
            while break_program == False:
                cls()
                print ('program is running, press "END" to stop')
                cur_time=int(time())
                firsttask=sorted(self)[0]
                if firsttask<=cur_time and not self.busy:
                    task=self.pop(firsttask)
                    self.busy=True
                    task['job']()
                    self.busy=False
                self.printlist()
                sleep(1)
            listener.join()


adb= Client(host='127.0.0.1', port=5037)
print(adb.version())
devices = adb.devices()

if len(devices) == 0:
    print("no devices")
    quit()

device=devices[0]

tl=Tasklist()

wheat=Crop(device, 'wheat', tl, growtime=2 , threshold=.9 , field=0, icon_x=125, icon_y=160, rel_x=100 , rel_y=600)
corn=Crop(device, 'corn', tl , growtime=5 , threshold=.8 , field=1, icon_x=200, icon_y=25, rel_x=-500 , rel_y=600)
soy=Crop(device, 'soy', tl, growtime=20 , threshold=.8 , field=0, icon_x=175, icon_y=300, rel_x=-250 , rel_y=700)

tl.start()
#wheat.harvest()
#corn.harvest()
#soy.harvest()
