"""278. First Bad Version."""
def solve(n: int, is_bad_version=None) -> int:
    if is_bad_version is None:
        is_bad_version = globals()['isBadVersion']
    left, right = 1, n
    while left < right:
        middle = (left + right) // 2
        if is_bad_version(middle):
            right = middle
        else:
            left = middle + 1
    return left

class Solution:
    def firstBadVersion(self, n: int) -> int:
        return solve(n)
