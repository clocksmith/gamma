def gcd(x, y):
    if y == 0:
        return x
    return gcd(y, x % y)

x, y = [int(i) for i in input().split()]
if x < y:
    x, y = y, x
print(gcd(x, y))
