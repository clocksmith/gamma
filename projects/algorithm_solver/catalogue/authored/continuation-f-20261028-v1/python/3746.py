"""Original frontend 3746 development candidate; qualification unknown."""

def solve(s):
    return abs(s.count('a') - s.count('b'))


class Solution:
    def minLengthAfterRemovals(self, s):
        return solve(s)
