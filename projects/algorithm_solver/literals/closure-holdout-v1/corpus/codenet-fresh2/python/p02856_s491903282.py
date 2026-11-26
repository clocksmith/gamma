import sys
def input():
    return sys.stdin.readline()[:-1]

M = int(input())
order = 0
total = 0
for i in range(M):
    d,c = map(int,input().split(' '))
    order += c
    total += d*c
print(order-1+(total-1)//9)