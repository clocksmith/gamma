from array import array

size = 300000
s = array('i', range(size + 1))
for i in range(size+1):
    if i % 7 != 1 and i % 7 != 6:
        s[i] = 0
s[1] = 0
sqrtn = int(round(size ** 0.5))
for i in range(6, sqrtn + 1):
    if s[i]:
        s[i * i: size + 1: i] = array('i', [0] * len(range(i*i, size+1, i)))
primes = list(filter(None, s))

while True:
    n = int(input())
    if n == 1: break
    i = 0
    ls = []
    for p in primes:
        if p > n: break
        if n % p == 0:
            ls.append(p)
    print(n, end="")
    print(':', end=" ")
    print(*ls)