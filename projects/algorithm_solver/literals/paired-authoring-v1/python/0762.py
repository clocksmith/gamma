class Solution:
    def countPrimeSetBits(self, left: int, right: int) -> int:
        primes = {2, 3, 5, 7, 11, 13, 17, 19}
        result = 0
        for value in range(left, right + 1):
            remaining = value
            bits = 0
            while remaining > 0:
                bits += remaining % 2
                remaining //= 2
            if bits in primes:
                result += 1
        return result
