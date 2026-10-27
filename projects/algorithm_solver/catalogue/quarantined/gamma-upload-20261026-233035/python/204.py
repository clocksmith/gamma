"""204. Count Primes."""
def solve(n: int) -> int:
    if n <= 2:
        return 0
    prime = bytearray(b'\x01') * n
    prime[0:2] = b'\x00\x00'
    limit = int(n ** 0.5)
    for value in range(2, limit + 1):
        if prime[value]:
            prime[value * value:n:value] = b'\x00' * (((n - 1 - value * value) // value) + 1)
    return sum(prime)

class Solution:
    def countPrimes(self, n: int) -> int:
        return solve(n)
