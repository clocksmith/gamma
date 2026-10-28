"""Original development candidate for frontend 3713; qualification pending."""

def solve(s):
    best = 0
    for left in range(len(s)):
        counts = [0] * 26
        distinct = maximum = 0
        for right in range(left, len(s)):
            index = ord(s[right]) - 97
            distinct += counts[index] == 0
            counts[index] += 1
            maximum = max(maximum, counts[index])
            if maximum * distinct == right - left + 1:
                best = max(best, right - left + 1)
    return best


class Solution:
    def longestBalanced(self, s):
        return solve(s)
