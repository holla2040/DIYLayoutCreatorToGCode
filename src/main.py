#!/usr/bin/env python3
import sys
from DIYLCToGCode import DIYLCToGCode
from pprint import pprint

if len(sys.argv) == 1:
    filename = 'test1.diy'
else:
    filename = sys.argv[1]

cam = DIYLCToGCode(filename)


