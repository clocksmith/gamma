A, B, K = map(int, input().split())
if K > B-A+1:
    K = B-A+1
t = set()
for i in range(A, A+K):
    t.add(i)
for i in range(B-K+1, B+1):
    t.add(i)
ans = list(t)
ans.sort()
for a in ans:
    print(a)