from collections import defaultdict,deque
import sys,heapq,bisect,math,itertools,string,queue,copy,time
sys.setrecursionlimit(10**8)
INF = float('inf')
mod = 10**9+7
eps = 10**-7
def inp(): return int(input())
def inpl(): return list(map(int, input().split()))
def inpl_str(): return list(input().split())

def calc_ar(bx,by,x,y):
    if bx == x:
        if y > by:
            return 1
        else:
            return 3
    else:
        if x > bx:
            return 0
        else:
            return 2

while True:
    N = inp()
    if N == 0:
        break
    else:
        lines = []

        for _ in range(N+1):
            m = inp()
            xys = [inpl() for _ in range(m)]

            dd = []
            for i in range(1,m):
                bx,by = xys[i-1]
                x,y = xys[i]
                if x == bx:
                    dd.append(abs(y-by))
                else:
                    dd.append(abs(x-bx))

            ar = []
            for i in range(2,m):
                x0,y0 = xys[i-2]
                x1,y1 = xys[i-1]
                x2,y2 = xys[i]
                ar01 = calc_ar(x0,y0,x1,y1)
                ar12 = calc_ar(x1,y1,x2,y2)
                ar.append((ar12 - ar01)%4)

            lines.append([dd]+[ar])


        for i in range(1,N+1):
            dd,ar = lines[i]
            if lines[0] == [dd]+[ar]:
                print(i)
            else:
                dd = list(reversed(dd))
                ar = [(a+2)%4 for a in reversed(ar)]
                if lines[0] == [dd]+[ar]:
                    print(i)



        print('+++++')

