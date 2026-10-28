"""Original frontend 3863 variant; qualification unknown."""

def solve(s):
    if all(a <= b for a, b in zip(s, s[1:])):
        return 0
    if len(s) == 2:
        return -1
    smallest, largest = min(s), max(s)
    if s[0] == smallest or s[-1] == largest:
        return 1
    if smallest in s[:-1] or largest in s[1:]:
        return 2
    return 3


class Solution:
    def minOperations(self, s):
        return solve(s)
