N = int(input())
V = [int(x) for x in input().split()]

print(sum(V) - (N * (N + 1) // 2))

