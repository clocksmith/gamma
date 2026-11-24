#!/usr/bin/env python

a, b, c = map(int, input().split())

if a%2 == 0 and a == b == c:
    print(-1)
    exit()

ans = 0 
while True:
    if a%2 == 1 or b%2 == 1 or c%2 == 1:
        print(ans)
        exit()
    ta = a 
    tb = b 
    tc = c 
    a = (tb+tc)//2
    b = (tc+ta)//2
    c = (ta+tb)//2
    ans += 1
