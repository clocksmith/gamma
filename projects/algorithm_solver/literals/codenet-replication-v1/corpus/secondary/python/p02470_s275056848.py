import sys
input = sys.stdin.readline
sys.setrecursionlimit(10 ** 7)

n = int(input())
prime_factors = []

i = 2
copy_n = n
while i ** 2 <= copy_n:
    ext = 0
    while copy_n % i == 0:
        ext += 1
        copy_n //= i
    if ext:
        prime_factors.append((i, ext))
    i += 1
if copy_n != 1:
    prime_factors.append((copy_n, 1))

for pf, _ in prime_factors:
    n *= (pf - 1)
    n //= pf
print(n)

