a = input().split(" ")
b = list(map(int, a))
c = int(input())
ans = 0
r = min([b[0] * 4, b[1] * 2, b[2]])
r2 = min([r * 2, b[3]])
if c % 2 == 1:
    ans += r
    c -= 1
ans += r2 * (c // 2)
print(int(ans))
