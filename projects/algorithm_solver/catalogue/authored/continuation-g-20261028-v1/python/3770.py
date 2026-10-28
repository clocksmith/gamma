from math import isqrt


def solve(n):
    prime = bytearray(b'\x01') * (n + 1)
    prime[0:2] = b'\x00\x00'
    for p in range(2, isqrt(n) + 1):
        if prime[p]:
            for x in range(p * p, n + 1, p):
                prime[x] = 0
    total = answer = 0
    for p in range(2, n + 1):
        if prime[p]:
            total += p
            if total > n:
                break
            if prime[total]:
                answer = total
    return answer


class Solution:
    def largestPrime(self, n):
        return solve(n)
