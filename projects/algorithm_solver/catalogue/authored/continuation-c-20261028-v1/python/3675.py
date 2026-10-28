def solve(s):
    return max((97-ord(c)) % 26 for c in s)

class Solution:
    def minOperations(self, s):
        return solve(s)
