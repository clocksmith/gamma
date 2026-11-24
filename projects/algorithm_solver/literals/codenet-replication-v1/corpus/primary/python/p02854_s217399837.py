import sys
input = sys.stdin.readline

N=int(input())
A=list(map(int,input().split()))
total = sum(A)
total *= 2
mindif = 1e12
sub = 0
for i in range(N):
    sub += 2 * A[i]
    dif = abs(total//2-sub)
    if dif < mindif:
        mindif = dif

print(mindif)
