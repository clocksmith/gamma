# -*- coding: utf-8 -*-

_sum = 0
_avg = 0
n = 0


while 1:
    try:
        _s, _a = [int(e) for e in input().split(',')]
        _sum += _s * _a
        _avg += _a
        n += 1
    except:
        print(_sum)
        print(int(_avg / n + 0.5))
        break