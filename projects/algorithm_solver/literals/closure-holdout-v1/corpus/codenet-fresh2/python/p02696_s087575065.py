A, B, N = map(int, input().split())

c = N // B

ans = 0

if c != 0:
    ans = int(A*(B-1)/B)
else:
    ans = int(A * N / B)

print(ans)

