# -*- coding: utf-8 -*-
"""
Dictionary - Map: Delete
http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=ITP2_8_B&lang=jp

"""
d = dict()
for _ in range(int(input())):
    op, key, x = (input() + ' 1').split()[:3]
    if op == '0':
        d[key] = x
    elif op == '1':
        print(d.get(key, 0))
    elif key in d:
        del d[key]

