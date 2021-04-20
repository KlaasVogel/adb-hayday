from os import path
from math import isclose,sqrt
from time import sleep
import cv2
import numpy as np
from ppadb.client import Client

class Adb_Device():
    def __init__(self):
        client=Client(host='127.0.0.1', port=5037)
        print(client.version())
        devices = client.devices()
        if len(devices) == 0:
            print("no devices")
            quit()
        self.device=devices[0]
        self.touch="/dev/input/event6"
        self.res_x, self.res_y = [1600,900]
        self.max=32767
        print(f'updating info for {self.device}')
        number=5
        touch_id=0
        lines=self.device.shell('getevent -p').split("\n")
        for line in lines:
            if "/dev/input" in line:
                number=line[-1]
            if "Touch" in line:
                touch_id=number
                self.touch=f"/dev/input/event{number}"
            if "max" in line and "ABS" in line and number==touch_id:
                values=line.split(', ')
                for value in values:
                    if "max" in value:
                        self.max=int(value[4:])
                        print(f"found max: {self.max}")

def correct(list1,list2):
    print('correct')
    newlist=[]
    dx=list2[0][0]-list1[0][0]
    dy=list2[0][1]-list1[0][1]
    for x,y in list1:
        newlist.append([x+dx,y+dy])
    return newlist

def trace(device, dev, waypoints, size=0, pressure=0):
    eventlist=[]
    for waypoint in waypoints:
        x,y=waypoint
        eventlist.append(f"{dev} 3 57 0")
        eventlist.append(f"{dev} 3 53 {int(x*32767/1600)}")
        eventlist.append(f"{dev} 3 54 {int(y*32767/900)}")
        if size:
            eventlist.append(f"{dev} 3 48 {size}")
        if pressure:
            eventlist.append(f"{dev} 3 58 {pressure}")
        eventlist.append(f"{dev} 0 2 0")
        eventlist.append(f"{dev} 0 0 0")
    eventlist.append(f"{dev} 3 57 -1")
    eventlist.append(f"{dev} 0 2 0")
    eventlist.append(f"{dev} 0 0 0")
    for event in eventlist:
        device.shell(event)


def move(device, x, y):
    print('moving')
    while (x or y):
        if x<0:
            dx=x if x>-600 else -600
        else:
            dx=x if x<600 else 600
        if y<0:
            dy=y if y>-300 else -300
        else:
            dy=y if y<300 else 300
        device.shell(f'input swipe {800+dx} {450+dy} 800 450 500')
        x=x-dx
        y=y-dy


def locate_item(device,template_file,threshold,one=False):
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
