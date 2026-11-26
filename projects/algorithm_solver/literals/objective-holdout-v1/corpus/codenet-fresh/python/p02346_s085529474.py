# -*- coding: utf-8 -*-
"""
http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=DSL_2_B&lang=jp

"""
import sys
from sys import stdin
input = stdin.readline


class BIT(object):
    def __init__(self, n):
        self.n = n
        self.bit = [0] * (n + 1)

    def sum(self, i):
        s = 0
        #  ?????????????????????????????¢?????????????¶?????????????
        while i > 0:
            s += self.bit[i]
#            i &= (i - 1)
            i -= (i & -i)

        return s

    def add(self, i, x):
        while i <= self.n:
            self.bit[i] += x
            i += (i & -i)

    def find(self, s, t):
        t_sum = self.sum(t)
        s_sum = self.sum(s - 1)
        return t_sum - s_sum


def main(args):
    n, q = map(int, input().split(' '))

    rq = BIT(n+1)
    for _ in range(q):
        com, x, y = map(int, input().split(' '))
        if com == 0:
            rq.add(x, y)
        elif com == 1:
            res = rq.find(x, y)
            print(res)


if __name__ == '__main__':
    main(sys.argv[1:])