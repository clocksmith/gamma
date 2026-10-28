"""Original development candidate for frontend 3722; qualification pending."""

def solve(s):
    best = s
    for width in range(1, len(s) + 1):
        best = min(best, s[:width][::-1] + s[width:], s[:-width] + s[-width:][::-1])
    return best


class Solution:
    def lexSmallest(self, s):
        return solve(s)
