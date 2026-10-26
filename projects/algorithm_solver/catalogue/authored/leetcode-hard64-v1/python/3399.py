"""3399. Smallest Substring With Identical Characters II: special-case alternation then binary search the longest allowed run."""


def solve(s: str, numOps: int) -> int:
    """O(n log n) time and O(n) auxiliary space. Inputs are preserved."""
    n = len(s)
    mismatches = sum((ord(character) - ord('0')) != index % 2 for index, character in enumerate(s))
    if min(mismatches, n - mismatches) <= numOps:
        return 1
    runs = []
    length = 0
    previous = ''
    for character in s:
        if character == previous:
            length += 1
        else:
            if length:
                runs.append(length)
            length = 1
            previous = character
    runs.append(length)
    left, right = 2, max(runs)
    while left < right:
        middle = (left + right) // 2
        required = sum(length // (middle + 1) for length in runs)
        if required <= numOps:
            right = middle
        else:
            left = middle + 1
    return left


class Solution:
    def minLength(self, s: str, numOps: int) -> int:
        return solve(s, numOps)
