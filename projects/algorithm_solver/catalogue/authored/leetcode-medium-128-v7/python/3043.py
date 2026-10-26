"""3043. Find the Length of the Longest Common Prefix: index integer prefixes of the first array and search the second from longest to shortest."""


def solve(arr1: list[int], arr2: list[int]) -> int:
    """O((n + m) * D) expected time and O(n * D) auxiliary space, where D is the maximum digit count; inputs are read-only."""
    prefixes = set()
    for number in arr1:
        value = number
        while value:
            prefixes.add(value)
            value //= 10
    best = 0
    for number in arr2:
        value = number
        length = len(str(number))
        while value:
            if value in prefixes:
                best = max(best, length)
                break
            value //= 10
            length -= 1
    return best


class Solution:
    def longestCommonPrefix(self, arr1: list[int], arr2: list[int]) -> int:
        return solve(arr1, arr2)
