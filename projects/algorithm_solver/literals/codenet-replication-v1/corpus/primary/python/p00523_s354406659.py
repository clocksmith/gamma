import sys

f = sys.stdin


def bisect(a,v):
    l,r = 0,len(a)-1
    
    while l != r:
        m = (l + r) // 2
        if a[m] < v:
            l = m + 1
        else:
            r = m
    return l

#n = int(f.readline())
a = list(map(int,f))
a[0] = 0
for i in range(1,len(a)):
    a[i] += a[i - 1]

sum_a = a[-1]
third = sum_a // 3

ret = []

for i in range(bisect(a, third)):
    nick1 = bisect(a, a[i] + third)
    
    for ni1 in (nick1-1,nick1):
        second = (sum_a - (a[ni1] - a[i])) // 2
        second = min(second,third)
        nick2 = bisect(a, a[ni1] + second)
        for ni2 in (nick2-1,nick2):
            if len(a) <= ni2:
                break
            piece1 = a[ni1] - a[i]
            piece2 = a[ni2] - a[ni1]
            piece3 = sum_a - piece1 - piece2
            ret.append(min(piece1,piece2,piece3))
print(max(ret))