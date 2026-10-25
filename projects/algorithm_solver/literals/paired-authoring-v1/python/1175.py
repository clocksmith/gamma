class Solution:
    def numPrimeArrangements(self, n: int) -> int:
        prime = [True] * (n + 1)
        prime[0] = False
        prime[1] = False
        candidate = 2
        while candidate * candidate <= n:
            if prime[candidate]:
                multiple = candidate * candidate
                while multiple <= n:
                    prime[multiple] = False
                    multiple += candidate
            candidate += 1
        prime_count = sum(prime)
        result = 1
        modulus = 1000000007
        for count in (prime_count, n - prime_count):
            for factor in range(2, count + 1):
                result = (result * factor) % modulus
        return result
