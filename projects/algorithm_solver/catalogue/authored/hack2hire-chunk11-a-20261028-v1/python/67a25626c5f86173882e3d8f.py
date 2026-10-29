"""Hack2Hire 67a25626c5f86173882e3d8f (Find Minimum Operations) over an INFERRED spec; qualification unknown."""


def solve(image):
    # the target is image reversed: target[j] == image[n - 1 - j]
    n, matched = len(image), 0
    for ch in image:
        if ch == image[n - 1 - matched]:
            matched += 1
    return n - matched


class Solution:
    def findMinimumOperations(self, image):
        return solve(image)
