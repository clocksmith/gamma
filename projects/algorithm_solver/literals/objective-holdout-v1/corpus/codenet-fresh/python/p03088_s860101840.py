import sys
import itertools
# import numpy as np
import time
import math
import heapq
from collections import defaultdict
sys.setrecursionlimit(10 ** 7)
 
INF = 10 ** 18
MOD = 10 ** 9 + 7
read = sys.stdin.buffer.read
readline = sys.stdin.buffer.readline
readlines = sys.stdin.buffer.readlines

# map(int, input().split())

N = int(input())
out = [ "AGC", "ACG", "GAC"]
from functools import *

def check(s):
    for i in range(4):
        t = list(s)
        if i >= 1:
            t[i - 1], t[i] = t[i], t[i - 1]
        if "".join(t).count('AGC') >= 1:
            return False
    return True

@lru_cache(None)
def dfs(n, s):
    if n == N:
        return 1
    res = 0
    for c in "ACGT":
        if not check(s + c):
            continue
        res += dfs(n + 1, s[1:] + c) % MOD
    return res

print(dfs(0, "TTT") % MOD)
    

