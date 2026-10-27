"""313. Super Ugly Number."""
def solve(n: int, primes: list[int]) -> int:
    values = [1] * n
    indices = [0] * len(primes)
    candidates = primes[:]
    for position in range(1, n):
        next_value = min(candidates)
        values[position] = next_value
        for index, prime in enumerate(primes):
            if candidates[index] == next_value:
                indices[index] += 1
                candidates[index] = prime * values[indices[index]]
    return values[-1]

class Solution:
    def nthSuperUglyNumber(self, n: int, primes: list[int]) -> int:
        return solve(n, primes)
