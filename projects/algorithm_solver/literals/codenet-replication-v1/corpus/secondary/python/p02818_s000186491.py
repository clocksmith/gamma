A, B, K = list(map(int, input().split()))

if (A > K):
    print(A - K, B)
elif (A + B > K):
    print(0, A + B - K)
else:
    print(0, 0)
