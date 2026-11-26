q = int(input())
a = [list(map(int,input().split())) for _ in range(q)]
import math
def f(a,b):
    k = int(math.sqrt(a*b))
    if k>=math.sqrt(a*b):
        k-=1
    if a==b:
        k = 2*min(a,b)-2
    elif min(a,b)+1==max(a,b):
        k = 2*min(a,b)-2
    else:
        if k*(k+1)>=a*b:
            k = 2*k-2
        else:
            k = 2*k-1
    return k
for a_ in a:
    print(f(a_[0],a_[1]))