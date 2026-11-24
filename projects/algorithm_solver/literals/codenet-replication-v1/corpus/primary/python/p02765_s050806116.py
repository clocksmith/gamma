n, r = map(int, input().split())

ans = r
if n < 10:
    ans += 100 * (10 - n)

print(ans)

