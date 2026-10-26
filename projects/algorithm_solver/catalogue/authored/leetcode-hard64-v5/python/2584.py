"""2584. Split the Array to Make Coprime Products. Join the first and last occurrence intervals of each prime factor."""


def solve(nums: list[int]) -> int:
    """O(M log log(M+2)+n log(M+1)) time and O(M+n) space, M=max(nums). Inputs are preserved."""
    maximum = max(nums)
    smallest = [0] * (maximum + 1)
    prime = 2
    while prime * prime <= maximum:
        if smallest[prime] == 0:
            for multiple in range(prime * prime, maximum + 1, prime):
                if smallest[multiple] == 0:
                    smallest[multiple] = prime
        prime += 1
    first = {}
    reach = list(range(len(nums)))
    for index, value in enumerate(nums):
        while value > 1:
            factor = smallest[value] or value
            beginning = first.setdefault(factor, index)
            reach[beginning] = index
            while value % factor == 0:
                value //= factor
    end = 0
    for index in range(len(nums) - 1):
        end = max(end, reach[index])
        if end == index:
            return index
    return -1


class Solution:
    def findValidSplit(self, nums: list[int]) -> int:
        return solve(nums)
