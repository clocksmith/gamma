import sys
input = lambda : sys.stdin.readline().rstrip()
sys.setrecursionlimit(max(1000, 10**9))
write = lambda x: sys.stdout.write(x+"\n")


def init(bit, values):
    for i,v in enumerate(values):
        update(bit,i,v)

#A1 ~ Aiまでの和 O(logN)
def query(bit,i):
    res_sum = 0
    while i > 0:
        res_sum += bit[i]
        i -= i&(-i)
    return res_sum

#Ai += x O(logN)
def update(bit,i,x):
    while i <= len(bit)-1:
        bit[i] += x
        i += i&(-i)
    return


n = int(input())
a = list(map(int, input().split()))
from collections import Counter
def sub(x):
    cumsum = [None] * n
    cumsum[0] = 1 if a[0]>=x else -1
    for i in range(1,n):
        cumsum[i] = cumsum[i-1] + (1 if a[i]>=x else -1)

    ### BIT 
    #A1 ... AnのBIT(1-indexed)
    bit = [0]*(2*n+2)
    update(bit, n+1, 1)
    ans = 0
    for v in cumsum:
        ans += query(bit, v+n+1)
        update(bit, n+v+1, 1)
    return ans

l = 0
r = 10**9+1
tmp = (n+1)*n//2
thre = tmp//2 + tmp%2
while l<r-1:
    m = (l+r)//2
    if sub(m)>=thre:
        l = m
    else:
        r = m
print(l)