# coding: utf-8

LIMIT = 999999

prime = [0, 1] + [0 if i % 2 == 0 else 1 for i in range(3, LIMIT + 1)]

for i in range(3, int(LIMIT ** 0.5) + 1):
    if prime[i - 1]:
        for j in range(i ** 2, LIMIT + 1, i):
            prime[j - 1] = 0

while True:
    try:
        n = int(input())
    except EOFError:
        break

    print(sum(prime[:n]))
