from ppadb.client import Client
from hd_objects import Crop

adb= Client(host='127.0.0.1', port=5037)
print(adb.version())
devices = adb.devices()

if len(devices) == 0:
    print("no devices")
    quit()

device=devices[0]

wheat=Crop(device, 'wheat' ,growtime=2 , threshold=.9 , field=0, icon_x=125, icon_y=160, rel_x=100 , rel_y=600)
corn=Crop(device, 'corn' ,growtime=5 , threshold=.8 , field=1, icon_x=200, icon_y=25, rel_x=-450 , rel_y=850)
soy=Crop(device, 'soy' ,growtime=20 , threshold=.8 , field=0, icon_x=175, icon_y=300, rel_x=-250 , rel_y=650)
# wheat.harvest()
wheat.harvest()
corn.harvest()
soy.harvest()
