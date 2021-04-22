from os import path
from math import isclose,sqrt
from time import sleep
import cv2
import numpy as np
from ppadb.client import Client

class Template():
    offset=[0,0]
    w,h=[0,0]
    data=[]
    def __init__(self, file):
        if path.isfile(file):
            self.data= cv2.imread(template_file)
            self.w,self.h=template.shape[:-1]
            if "_C" in template_file:
                self.offset=[w/2,h/2]
            if "_R" in template_file:
                self.offset[0]=self.w
            if "O_" in template_file:
                self.offset[1]=self.h


class Adb_Device():
    device=None
    touch="/dev/input/event6"
    res_x, res_y= [1600,900]
    max=32767

    def __init__(self):
        client=Client(host='127.0.0.1', port=5037)
        print(client.version())
        devices = client.devices()
        if len(devices) == 0:
            print("no devices")
            quit()
        self.device=devices[0]
        print(f'updating info for {self.device}')
        number=5
        touch_id=0
        lines=self.device.shell('getevent -p').split("\n")
        for line in lines:
            if "/dev/input" in line:
                number=line[-1]
            if "Touch" in line:
                touch_id=number
                self.touch=f"sendevent /dev/input/event{number}"
            if "max" in line and "ABS" in line and number==touch_id:
                values=line.split(', ')
                for value in values:
                    if "max" in value:
                        self.max=int(value[4:])
                        print(f"found max: {self.max}")

    @staticmethod
    def correct(list1,list2):
        print('correct')
        newlist=[]
        dx=list2[0][0]-list1[0][0]
        dy=list2[0][1]-list1[0][1]
        for x,y in list1:
            newlist.append([x+dx,y+dy])
        return newlist

    def release_all(self):
        shellcmd= f"{self.touch} 3 57 -1  && {self.touch} 0 2 0 && {self.touch} 0 0 0"
        self.device.shell(shellcmd)

    def zoom_out(self):
        y=0.35
        x_c=.5
        dx=0.25
        steps=[]
        for i in range(10):
            x1=x_c-dx*(10-i)/11
            x2=x_c+dx*(10-i)/11
            steps.append(f"{self.touch} 3 57 0")
            steps.append(f"{self.touch} 3 53 {int(x1*self.max)}")
            steps.append(f"{self.touch} 3 54 {int(y*self.max)}")
            steps.append(f"{self.touch} 0 2 0")
            steps.append(f"{self.touch} 3 57 1")
            steps.append(f"{self.touch} 3 53 {int(x2*self.max)}")
            steps.append(f"{self.touch} 3 54 {int(y*self.max)}")
            steps.append(f"{self.touch} 0 2 0")
            steps.append(f"{self.touch} 0 0 0")
        shellcmd=" && ".join(steps)
        self.device.shell(shellcmd)
        self.release_all()
        self.release_all()

    def trace(self, waypoints, size=0, pressure=0):
        eventlist=[]
        for waypoint in waypoints:
            x,y=waypoint
            eventlist.append(f"{self.touch} 3 57 0")
            eventlist.append(f"{self.touch} 3 53 {int(x*self.max/self.res_x)}")
            eventlist.append(f"{self.touch} 3 54 {int(y*self.max/self.res_y)}")
            if size:
                eventlist.append(f"{self.touch} 3 48 {size}")
            if pressure:
                eventlist.append(f"{self.touch} 3 58 {pressure}")
            eventlist.append(f"{self.touch} 0 2 0")
            eventlist.append(f"{self.touch} 0 0 0")
        eventlist.append(f"{self.touch} 3 57 -1")
        eventlist.append(f"{self.touch} 0 2 0")
        eventlist.append(f"{self.touch} 0 0 0")
        # for event in eventlist:
        #     self.device.shell(event)
        shellcmd=" & ".join(eventlist)
        print(shellcmd)
        # self.device.shell(shellcmd)

    def move(self, x, y):
        print('moving')
        border_x=self.res_x*600/1600
        border_y=self.res_y*300/900
        while (x or y):
            if x<0:
                dx=x if x>-border_x else -border_x
            else:
                dx=x if x<border_x else border_x
            if y<0:
                dy=y if y>-border_y else -border_y
            else:
                dy=y if y<border_y else border_y
            device.shell(f'input swipe {self.res_x/2+dx} {self.res_y/2+dy} 800 450 500')
            x=x-dx
            y=y-dy

    def locate_item(self,templates,threshold=0.75,margin=0.15,one=False,show=True):
        screencap = device.screencap()
        # screenshot_file=path.join('images','screen.png')
        result_file=path.join('images','result.png')
        loclist=[]

        # with open(screenshot_file, 'wb') as f:
        #     f.write(screencap)
        # sleep(.2)
        # # device.shell('input touchscreen swipe 500 500 500 500 2000')
        # img=cv2.imread(screenshot_file)
        img_array=np.array(screencap)
        img=cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        for template in templates:
                result = cv2.matchTemplate(img, template.data, cv2.TM_CCOEFF_NORMED)
                max=np.max(result)
                if (max>=threshold):
                    min=max-margin if (max-margin >= threshold) else threshold
                    loc=np.where(result >= min)
                    if len(loc[0]):
                        for pt in zip(*loc[::-1]):  # Switch collumns and rows
                            for location in loclist:
                                x,y=np.add(pt,template.offset)
                                print(pt)
                                print(x,y)
                                sleep(10)
                                if not (isclose(x, location[0], abs_tol=90) and isclose(y, location[1], abs_tol=40)):
                                    print(f"found on {x},{y} ")
                                    cv2.rectangle(img, pt, (pt[0] + template.w, pt[1] + template.h), (0, 0, 255), 2)
                                    cv2.circle(img, (x,y), 10, (0,255,0), -1)
                                    loclist.append([x,y])
        # cv2.imwrite(result_file, img)
        if show:
            # cv2.imshow('Template',template)
            cv2.imshow('Example - Show image in window',img)
            # cv2.waitKey(0) # waits until a key is pressed
            # cv2.destroyAllWindows() # destroys the window showing image
        if one:
            winner=loclist[0]
            score=99999
            for loc in loclist:
                x,y=loc
                newscore=(800-x)*(800-x)+(450-y)*(450-y)
                if newscore<score:
                    winner=[x,y]
                    score=newscore
            return winner
        return loclist


    def locate_item2(self,templates,threshold,one=False):
        screencap = device.screencap()

        screenshot_file=path.join('images','screen.png')
        result_file=path.join('images','result.png')
        with open(screenshot_file, 'wb') as f:
            f.write(screencap)
        # device.shell('input touchscreen swipe 500 500 500 500 2000')
        sleep(.2)
        img=cv2.imread(screenshot_file)
        template= cv2.imread(template_file)
        w,h=template.shape[:-1]

        res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        if not threshold:
            threshold=np.max(res)
            print(f'max is {threshold}')
            # cv2.imshow('Example - Show image in window',res)
            # cv2.waitKey(0) # waits until a key is pressed
            # cv2.destroyAllWindows() # destroys the window showing image
        loc = np.where(res >= threshold)
        # print(loc)
        if len(loc[0]):
            loclist=[]
            for pt in zip(*loc[::-1]):  # Switch collumns and rows
                for location in loclist:
                    if (isclose(pt[0], location[0], abs_tol=90) and isclose(pt[1], location[1], abs_tol=40)):
                        # print(f"{pt} double on {location}")
                        break
                else:
                    print(f"found on {pt}")
                    cv2.rectangle(img, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)
                    loclist.append(pt)
            cv2.imwrite(result_file, img)
            if one:
                winner=loclist[0]
                score=99999
                for loc in loclist:
                    x,y=loc
                    newscore=(800-x)*(800-x)+(450-y)*(450-y)
                    if newscore<score:
                        winner=[x,y]
                        score=newscore
                return winner
            return loclist
        # else:
        #     cv2.imshow('Template',template)
        #     cv2.imshow('Example - Show image in window',res)
        #     cv2.waitKey(0) # waits until a key is pressed
        #     cv2.destroyAllWindows() # destroys the window showing image
        return []
        # for pt in zip(*loc[::-1]):  # Switch collumns and rows
        #     cv2.rectangle(img, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)
