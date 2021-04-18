
from hd_objects import Crop, Production, Pen
from tasks import Tasklist
from adb_functions import load_adb

device=load_adb()
tl=Tasklist()

carrot=Crop(device, 'carrot', tl, growtime=10 , threshold=.55 , field=0, icon_x=375, icon_y=10, rel_x=-75 , rel_y=300)
wheat=Crop(device, 'wheat', tl, growtime=2 , threshold=.85 , field=0, icon_x=125, icon_y=160, rel_x=100 , rel_y=600)
corn=Crop(device, 'corn', tl , growtime=5 , threshold=.8 , field=1, icon_x=200, icon_y=25, rel_x=-400 , rel_y=550)
soy=Crop(device, 'soy', tl, growtime=20 , threshold=.8 , field=0, icon_x=175, icon_y=300, rel_x=-250 , rel_y=700)

mill1=Production(device, 'feed mill', tl, threshold=.4, icon_x=0, icon_y=-200, rel_x=-800, rel_y=-100)
mill1.add(product='cow feed', worktime=10, icon_x=-200, icon_y=-200, second_menu=False)
mill1.add(product='chicken feed', worktime=5, icon_x=0, icon_y=-250, second_menu=False)
mill1.add(product='chicken feed', worktime=5, icon_x=0, icon_y=-250, second_menu=False)
mill1.add(product='pig feed', worktime=20, icon_x=-300, icon_y=-125, second_menu=False)
mill1.add(product='chicken feed', worktime=5, icon_x=0, icon_y=-250, second_menu=False)
mill1.add(product='chicken feed', worktime=5, icon_x=0, icon_y=-250, second_menu=False)
# mill1.start()

coop=Pen(device, tl, animal='chicken', product='egg', eattime=20, threshold=.7, size=300, icon_x=0, icon_y=-100, rel_x=-1000, rel_y=200)

tl.start()
#wheat.harvest()
#corn.harvest()
#soy.harvest()
