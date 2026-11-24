A, B, M = map(int, input().split())
price_A = list(map(int, input().split()))
price_B = list(map(int, input().split()))

ans = min(price_A) + min(price_B)

for _ in range(M):
    x, y, c = map(int, input().split())
    tmp = price_A[x-1] + price_B[y-1] - c
    if ans > tmp:
        ans = tmp
        
print(ans)