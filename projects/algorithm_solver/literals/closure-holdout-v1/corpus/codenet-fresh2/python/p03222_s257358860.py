'''
自宅用PCでの解答
'''
import math
#import numpy as np
import itertools
import queue
import bisect
from collections import deque,defaultdict
import heapq as hpq
from sys import stdin,setrecursionlimit
#from scipy.sparse.csgraph import dijkstra
#from scipy.sparse import csr_matrix
ipt = stdin.readline
setrecursionlimit(10**7)
mod = 10**9+7
dir = [(-1,0),(0,-1),(1,0),(0,1)]
alp = "abcdefghijklmnopqrstuvwxyz"

def main():
    h,w,k = map(int,ipt().split())
    nm = [1,1,2,3,5,8,13,21,34]
    dp = [0]*(w+2)
    dp[1] = 1
    for i in range(h):
        ndp = [0]*(w+2)
        for j in range(1,w+1):
            ndp[j] = dp[j]*nm[j-1]*nm[w-j]+dp[j-1]*nm[j-2]*nm[w-j]+dp[j+1]*nm[j-1]*nm[w-j-1]
            ndp[j] %= mod
        dp = ndp*1
#        print(dp)

    print(dp[k])


    return None

if __name__ == '__main__':
    main()
