N, K = list(map(int, input().split()))
H = sorted(list(map(int, input().split())))
if K>=N:
    print(0)
else:
    remain = H[:N-K]
    print(sum(remain))