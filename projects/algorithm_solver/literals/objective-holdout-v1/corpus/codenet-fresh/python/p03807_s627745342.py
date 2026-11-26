# A - Addition

N = int(input())
A = list(map(int, input().split()))
k = 0
for i in range(N):
    k = (A[i] + k) % 2
k *= int(N!=1)
ans = ['YES', 'NO']
print(ans[k])