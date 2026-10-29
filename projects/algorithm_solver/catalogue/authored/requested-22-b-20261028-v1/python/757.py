"""Original frontend 757 variant; qualification unknown."""

def solve(intervals):
    count = 0
    first = second = -1
    for start, end in sorted(intervals, key=lambda interval: (interval[1], -interval[0])):
        if start > second:
            count += 2
            first, second = end - 1, end
        elif start > first:
            count += 1
            first, second = second, end
    return count


class Solution:
    def intersectionSizeTwo(self, intervals):
        return solve(intervals)
