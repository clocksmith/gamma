"""2741. Special Permutations: count compatible permutations by used-index masks and their final index."""


def solve(nums: list[int]) -> int:
    """O(n * n * 2^n) time and O(n * 2^n) auxiliary space; inputs are read-only."""
    modulus = 1_000_000_007
    size = len(nums)
    compatible = [0] * size
    for left in range(size):
        for right in range(size):
            if left != right and (nums[left] % nums[right] == 0 or nums[right] % nums[left] == 0):
                compatible[left] |= 1 << right
    ways = [[0] * size for _ in range(1 << size)]
    for index in range(size):
        ways[1 << index][index] = 1
    for mask in range(1, 1 << size):
        for last, count in enumerate(ways[mask]):
            if count == 0:
                continue
            remaining = compatible[last] & ~mask
            while remaining:
                bit = remaining & -remaining
                following = bit.bit_length() - 1
                target = mask | bit
                ways[target][following] = (ways[target][following] + count) % modulus
                remaining -= bit
    return sum(ways[-1]) % modulus


class Solution:
    def specialPerm(self, nums: list[int]) -> int:
        return solve(nums)
