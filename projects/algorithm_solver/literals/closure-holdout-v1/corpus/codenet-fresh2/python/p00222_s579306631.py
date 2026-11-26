from math import sqrt, ceil

N = 10100000
temp = [True]*(N+1)
temp[0] = temp[1] = False
for i in range(2, ceil(sqrt(N+1))):
    if temp[i]:
        temp[i+i::i] = [False]*(len(temp[i+i::i]))

quadruplet = [True, False, True, False, False, False, True, False,True]
ans = [0]*N
for i in range(8,N):
    if temp[i] and temp[i-8:i+1] == quadruplet: ans[i] = i
    else: ans[i] = ans[i-1]
while True:
    n = int(input())
    if not n: break
    print(ans[n])
