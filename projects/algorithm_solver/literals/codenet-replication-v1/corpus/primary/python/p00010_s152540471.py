#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys
import math

n = int(input())

for data in sys.stdin:
    x1, y1, x2, y2, x3, y3 = map(float, data.split())
    a1 = x2 - x1
    b1 = y2 - y1
    a2 = x3 - x1
    b2 = y3 - y1
    px = (b2 * (a1 * a1 + b1 * b1) - b1 * (a2 * a2 + b2 * b2)) / (2 * (a1 * b2 - a2 * b1))
    py = (a1 * (a2 * a2 + b2 * b2) - a2 * (a1 * a1 + b1 * b1)) / (2 * (a1 * b2 - a2 * b1))
    r = math.sqrt(px * px + py * py)
    px += x1
    py += y1
    print("{0:.3f} {1:.3f} {2:.3f}".format(px, py, r))