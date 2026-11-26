import sys

N, K = map(int, input().split())
B = list(map(int, sys.stdin.readline().rsplit()))

res = 10 ** 18
for i in range(2 ** N):
    cnt = 0
    for j in range(N):
        # print(bin(i), bin(i >> j))
        if (i >> j) & 1:
            cnt += 1
    # print(cnt)
    if cnt != K:
        continue
    
    A = B[::]
    cnt = 0
    maxi = A[0] - 1
    for j in range(N):
        if (i >> j) & 1:
            if A[j] <= maxi:
                cnt += (maxi + 1) - A[j]
                A[j] = maxi + 1

        maxi = max(maxi, A[j])

    res = min(res, cnt)

print(res)
# print(A)
