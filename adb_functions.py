from os import path
from math import isclose
from time import sleep
import cv2
import numpy as np

def correct(list1,list2):
    print('correct')
    newlist=[]
    dx=list2[0][0]-list1[0][0]
    dy=list2[0][1]-list1[0][1]
    for x,y in list1:
        newlist.append([x+dx,y+dy])
    return newlist


def get_dev(device):
    print('getting info')
    number=5
    test=device.shell('getevent -p')
    lines=test.split("\n")
    for line in lines:
        if "/dev/input" in line:
            number=line[-1]
        if "Touch" in line:
            return f"sendevent /dev/input/event{number}"
    return "sendevent /dev/input/event6"


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


def locate_item(device,template_file,threshold):
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
    loc = np.where(res >= threshold)
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
        return loclist
    return []
    # for pt in zip(*loc[::-1]):  # Switch collumns and rows
    #     cv2.rectangle(img, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)
