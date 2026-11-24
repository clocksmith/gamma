from sys import setrecursionlimit, exit

n, m = map(int, input().split())
a = [int(x) // 2 for x in input().split()]

t = 0
while a[0] % 2 == 0:
    a[0] //= 2
    t += 1

for i in range(1, n):
    t2 = 0
    while a[i] % 2 == 0:
        a[i] //= 2
        t2 += 1
    if t2 != t:
        print(0)
        exit()

def gcd(x, y):
    return gcd(y, x%y) if y else x
def lcm(x, y):
    return x // gcd(x, y) * y

m >>= t
l = 1
for i in a:
    l = lcm(l, i)
    if l > m:
        print(0)
        exit()
print((m // l + 1) // 2)