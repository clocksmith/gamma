n = int(input())
for _ in range(n):
    K, P = map(int, input().split())
    a = K % P
    print(P * (a == 0) + (a) * (a != 0))