"""Hack2Hire 6a7cd372d713d873ca7ac6ef (Find Free Bucket ID Ranges, level 1) over an INFERRED spec; qualification unknown."""


def solve(bucketRanges):
    spans = sorted((int(start), int(end)) for _, start, end in bucketRanges)
    result = []
    cursor = 0
    for start, end in spans + [(1000, 1000)]:
        if start - cursor >= 1:
            result.append([str(cursor), str(start - 1)])
        cursor = end + 1
    return result


class Solution:
    def findFreeRanges(self, bucketRanges):
        return solve(bucketRanges)
