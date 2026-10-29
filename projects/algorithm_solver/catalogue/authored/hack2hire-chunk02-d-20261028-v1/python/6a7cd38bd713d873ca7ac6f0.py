"""Hack2Hire 6a7cd38bd713d873ca7ac6f0 (Find Free Bucket ID Ranges, level 2) over an INFERRED spec; qualification unknown."""


def solve(bucketRanges, minSize):
    spans = sorted((int(start), int(end)) for _, start, end in bucketRanges)
    result = []
    cursor = 0
    for start, end in spans + [(1000, 1000)]:
        if start - cursor >= max(1, minSize):
            result.append([str(cursor), str(start - 1)])
        cursor = end + 1
    return result


class Solution:
    def findFreeRanges(self, bucketRanges, minSize):
        return solve(bucketRanges, minSize)
