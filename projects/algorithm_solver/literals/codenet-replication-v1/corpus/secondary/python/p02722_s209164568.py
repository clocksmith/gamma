N = int(input())


def make_divisors(n):
    divisors = []
    for i in range(1, int(n**0.5)+1):
        if n % i == 0:
            divisors.append(i)
            if i != n // i:
                divisors.append(n//i)

    # divisors.sort()
    return divisors


C = set(make_divisors(N) + make_divisors(N-1))
C.discard(1)


def f(x, k):
    if x % k == 0:
        return x//k
    else:
        return x % k


ans = 0
for i in C:
    x = N
    c = 0
    while x >= i:
        c += 1
        x = f(x, i)
    if x == 1:
        ans += 1

print(ans)
