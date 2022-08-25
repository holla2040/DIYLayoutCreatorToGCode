#!/usr/bin/env python3

RAPIDHEIGHT=0.5
DRILLSPEED=10
DRILLHEIGHT=-0.1
CUTSPEED=20

import xmltodict,pprint,sys

import numpy as np

# https://codereview.stackexchange.com/questions/28207/finding-the-closest-point-to-a-list-of-points
def closest_point(point, points):
    points = np.asarray(points)
    deltas = points - point
    dist_2 = np.einsum('ij,ij->i', deltas, deltas)
    return np.argmin(dist_2)

if len(sys.argv) == 1:
    filename = 'bassmanMicroLTP.diy'
else:
    filename = sys.argv[1]

with open(filename, 'r', encoding='utf-8') as file:
	xml = file.read()
outfn = filename.replace('diy','nc')
jsonfn = filename.replace('diy','json')

dict = xmltodict.parse(xml)

# pprint.pprint(dict, indent=2)
with open(jsonfn, "w") as json_file:
    pprint.pprint(dict, json_file)


project     = dict['project']
components  = project['components']
board       = components['diylc.boards.BlankBoard']

boardw = abs(float(board['firstPoint']['@x']) - float(board['secondPoint']['@x']))
boardh = abs(float(board['firstPoint']['@y']) - float(board['secondPoint']['@y']))

x1 = float(board['firstPoint']['@x'])
y1 = float(board['firstPoint']['@y'])
x2 = float(board['secondPoint']['@x'])
y2 = float(board['secondPoint']['@y'])

bounds = ((0,0),(boardw,0),(boardw,boardh),(0,boardh),(0,0))

left   = float(board['firstPoint']['@x'])
bottom = float(board['secondPoint']['@y'])

eyelets = []
try:
    for eyelet in components['diylc.connectivity.Eyelet']:
        eyelets.append((float(eyelet['point']['@x'])-left,bottom-float(eyelet['point']['@y'])))
except:
    pass

turrets = []
for turret in components['diylc.connectivity.Turret']:
    turrets.append((float(turret['point']['@x'])-left,bottom-float(turret['point']['@y'])))


'''
print(project['author'])
print(boardw,boardh)
print(eyelets)
print(turrets)
'''


f = open(outfn,"w")

setup="(%s)\n(%s)\n\
G0 G17 G80 G90 G54 G20\n\
M6 T0\n\
G0 Z%f\n\n\
M3 G4P2000\n\n"%(filename,project['author'],RAPIDHEIGHT)
f.write(setup)


f.write("(turrets)\n")
point = (0,0)
while len(turrets):
    i = closest_point(point, turrets)
    point = turrets.pop(i)
    #print(i, point)
    x,y = point

    f.write("G0 X%f Y%f\n"%(x,y))
    f.write("G1 Z%f F%f\n"%(DRILLHEIGHT,DRILLSPEED))
    f.write("G1 Z%f F%f\n"%(-DRILLHEIGHT,DRILLSPEED))
    f.write("G0 Z%f\n\n"%(RAPIDHEIGHT))


f.write("G0 X%f Y%f\n"%(bounds[0]))
f.write("G1 Z%f F%f\n"%(DRILLHEIGHT,DRILLSPEED))
for p in bounds:
    f.write("G1 F%f X%f Y%f\n"%(CUTSPEED,p[0],p[1]))
f.write("G1 Z%f F%f\n"%(-DRILLHEIGHT,DRILLSPEED))
f.write("G0 Z%f\n\n"%(RAPIDHEIGHT))




teardown="M5\n\nM30\n"
f.write(teardown)

f.close()
