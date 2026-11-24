N = int(input())
d = list(map(int, input().split()))

sort_d = sorted(d)
print(sort_d[int(N/2)] - sort_d[int(int(N/2)-1)])