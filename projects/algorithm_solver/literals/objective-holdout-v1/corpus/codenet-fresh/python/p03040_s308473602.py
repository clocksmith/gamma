# python 3.4.3
import sys
input = sys.stdin.readline

# -------------------------------------------------------------
# library
# -------------------------------------------------------------



# -------------------------------------------------------------
# main
# -------------------------------------------------------------
import heapq

L,R = [10**15],[10**15]
lenL,lenR = 1,1
sumL,sumR = 0,0
y = 0

Q = int(input())
for i in range(Q):
    query = list(map(int,input().split()))
    if len(query) == 1:
        x = -L[0]
        f = sumR - sumL + y
        if lenL != lenR:
            f += x
        print("{} {}".format(x, f))
    else:
        q,a,b = query
        y += b
        if lenL > lenR:
            sumL += a
            a = -heapq.heappushpop(L, -a)
            sumL -= a
            heapq.heappush(R, a)
            sumR += a
            lenR += 1
        else:
            sumR += a
            a = heapq.heappushpop(R, a)
            sumR -= a
            heapq.heappush(L, -a)
            sumL += a
            lenL += 1


