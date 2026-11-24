# coding: utf-8
# Your code here!
import sys
read = sys.stdin.read
readline = sys.stdin.readline




def solve():
    def normalize(v,basis):
        for b in basis:
            if v > v^b: v ^= b
        return v
    
    n, = map(int,readline().split())
    *a, = map(int,readline().split())
    s = input()
    
    basis = []
    b0 = []

    for e,si in zip(a[::-1],s[::-1]):
        if si=="0":
        	for b in basis:
        	    if e > e^b: e ^= b
        	if e: basis.append(e)

        if si=="1":
            v = normalize(e,basis)
            if v!=0:
                print(1)
                return

    
    print(0)
    return
        
        


t = int(input())
for _ in range(t):
    solve()









