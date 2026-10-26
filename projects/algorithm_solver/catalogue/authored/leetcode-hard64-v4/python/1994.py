"""1994. The Number of Good Subsets."""


def solve(nums: list[int]) -> int:
    """Square-free prime-mask DP and independent ones; O(n+30*2^10) time and O(2^10) space. Inputs are preserved."""
    modulus = 1_000_000_007
    frequency = [0] * 31
    for value in nums:
        frequency[value] += 1
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    ways = [0] * (1 << len(primes))
    ways[0] = 1
    for value in range(2, 31):
        if not frequency[value]:
            continue
        mask = 0
        valid = True
        for index, prime in enumerate(primes):
            if value % (prime * prime) == 0:
                valid = False
                break
            if value % prime == 0:
                mask |= 1 << index
        if not valid:
            continue
        for previous in range(len(ways) - 1, -1, -1):
            if previous & mask == 0:
                following = previous | mask
                ways[following] = (ways[following] + ways[previous] * frequency[value]) % modulus
    answer = sum(ways[1:]) % modulus
    for _ in range(frequency[1]):
        answer = answer * 2 % modulus
    return answer


class Solution:
    def numberOfGoodSubsets(self, nums: list[int]) -> int:
        return solve(nums)
