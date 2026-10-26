"""2572. Count the Number of Square-Free Subsets: combine disjoint prime masks while treating repeated nonunit values as exclusive choices."""


def solve(nums: list[int]) -> int:
    """O(n + 30 * 2^10) time and O(2^10) auxiliary space; inputs are read-only."""
    modulus = 1_000_000_007
    primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29)
    counts = [0] * 31
    for value in nums:
        counts[value] += 1
    ways = [0] * (1 << len(primes))
    ways[0] = pow(2, counts[1], modulus)
    for value in range(2, 31):
        if not counts[value]:
            continue
        mask = 0
        for bit, prime in enumerate(primes):
            if value % (prime * prime) == 0:
                break
            if value % prime == 0:
                mask |= 1 << bit
        else:
            updated = ways[:]
            for used, count in enumerate(ways):
                if used & mask == 0:
                    target = used | mask
                    updated[target] = (updated[target] + count * counts[value]) % modulus
            ways = updated
    return (sum(ways) - 1) % modulus


class Solution:
    def squareFreeSubsets(self, nums: list[int]) -> int:
        return solve(nums)
