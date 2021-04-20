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
    try:
        if key == keyboard.Key.end or key.char == 'q':
            print ('end pressed')
            break_program = True
            return False
        if key.char == 'p':
            print('pause?')
            paused=False if paused else True
    except:
        return True


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
                if not paused:
                    firsttask=sorted(self)[0]
                    if firsttask<=cur_time and not self.busy:
                        task=self.pop(firsttask)
                        self.busy=True
                        task['job']()
                        self.busy=False
                self.printlist()
                sleep(1)
            listener.join()
