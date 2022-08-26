#!/usr/bin/env python3
import xmltodict
import numpy as np
from pprint import pprint

exec(open("config.txt").read())

class DIYLCToGCode():
    def __init__(self, filename):
        self.filename = filename
        self.boards   = []
        self.eyelets  = []
        self.turrets  = []

        with open(self.filename, 'r', encoding='utf-8') as file:
            xml = file.read() 
        jsonfn = self.filename.replace('diy','json')

        dict = xmltodict.parse(xml)

        with open(jsonfn, "w") as json_file:
            pprint(dict, json_file)

        self.project     = dict['project']
        self.components  = self.project['components']

        board       = self.components['diylc.boards.BlankBoard']
        
        if isinstance(board,list):
            for b in board:
                if b['type'] == 'SQUARE':
                    self.boards.append(b)
                else:
                    print("skipping board %s, not square"%b['name'])
        else:
            if board['type'] == 'SQUARE':
                self.boards.append(board)
            else:
                print("skipping board %s, not square"%b['name'])

        try:
            for eyelet in self.components['diylc.connectivity.Eyelet']:
                self.eyelets.append((float(eyelet['point']['@x']),float(eyelet['point']['@y'])))
        except:
            pass
    
        try:
            for turret in self.components['diylc.connectivity.Turret']:
                self.turrets.append((float(turret['point']['@x']),float(turret['point']['@y'])))
        except:
            pass

        self.processBoards()






    # https://codereview.stackexchange.com/questions/28207/finding-the-closest-point-to-a-list-of-points
    def closest_point(self,point,points):
        points = np.asarray(points)
        deltas = points - point
        dist_2 = np.einsum('ij,ij->i', deltas, deltas)
        return np.argmin(dist_2)

    def pointInRect(self,point,rect):
        x1, y1, w, h = rect
        x2, y2 = x1+w, y1+h
        x, y = point
        #print(x,x1,x2,"   ",y,y1,y2)
        if (x1 < x and x < x2):
            if (y1 < y and y < y2):
                return True
        return False


    def processBoards(self):
        for board in self.boards:
            self.ncfn = self.filename.replace('.diy','-%s.nc'%board['name'])
            self.ncf  = open(self.ncfn,"w")
            print("processing board %s"%board['name'])

            boardw = abs(float(board['firstPoint']['@x']) - float(board['secondPoint']['@x']))
            boardh = abs(float(board['firstPoint']['@y']) - float(board['secondPoint']['@y']))

            x1 = float(board['firstPoint']['@x'])
            y1 = float(board['firstPoint']['@y'])
            x2 = float(board['secondPoint']['@x'])
            y2 = float(board['secondPoint']['@y'])

            bounds = ((0,0),(boardw,0),(boardw,boardh),(0,boardh),(0,0))
            left   = float(board['firstPoint']['@x'])
            top    = float(board['firstPoint']['@y'])
            bottom = float(board['secondPoint']['@y'])

            self.ncf.write(SETUP)
            self.ncf.write("M6 T0 ; select tool 0 eyelet %0.3f drill\n"%EYELETDIA) 
            self.ncf.write("M3\n") 

            # finding eyelets on this board
            locations = []
            for eyelet in self.eyelets:
                if self.pointInRect(eyelet,(left,top,boardw,boardh)):
                    locations.append(eyelet)
                
            self.ncf.write("(eyelets)\n") 
            point = (0,0)
            while len(locations):
                i = self.closest_point(point,locations)
                point = locations.pop(i)
                x,y = point
                x = x - left
                y = bottom - y

                self.ncf.write("G0 X%f Y%f\n"%(x,y))
                self.ncf.write("G1 Z%f F%f\n"%(DRILLDEPTH,DRILLSPEED))
                self.ncf.write("G1 Z%f F%f\n"%(-DRILLDEPTH,DRILLSPEED))
                self.ncf.write("G0 Z%f\n\n"%(CLEARANCE))

            # finding turrets on this board
            self.ncf.write("M6 T1 ; select tool 1 turret %0.3f drill\n"%TURRETDIA) 
            locations = []
            for turret in self.turrets:
                if self.pointInRect(turret,(left,top,boardw,boardh)):
                    locations.append(turret)
                
            self.ncf.write("(turret)\n") 
            point = (0,0)
            while len(locations):
                i = self.closest_point(point,locations)
                point = locations.pop(i)
                x,y = point
                x = x - left
                y = bottom - y

                self.ncf.write("G0 X%f Y%f\n"%(x,y))
                self.ncf.write("G1 Z%f F%f\n"%(DRILLDEPTH,DRILLSPEED))
                self.ncf.write("G1 Z%f F%f\n"%(-DRILLDEPTH,DRILLSPEED))
                self.ncf.write("G0 Z%f\n\n"%(CLEARANCE))


            if OUTLINE:
                self.ncf.write("M6 T2 ; select tool 2 outline %0.3f endmill"%ENDMILLDIA)
                self.ncf.write("G0 X%f Y%f\n"%(bounds[0]))
                self.ncf.write("G1 Z%f F%f\n"%(DRILLDEPTH,CUTSPEED))
                for p in bounds:
                    self.ncf.write("G1 F%f X%f Y%f\n"%(CUTSPEED,p[0],p[1]))
                self.ncf.write("G1 Z%f F%f\n"%(-DRILLDEPTH,CUTSPEED))
                self.ncf.write("G0 Z%f\n\n"%(CLEARANCE))

            self.ncf.write(SHUTDOWN)




            self.ncf.close()


