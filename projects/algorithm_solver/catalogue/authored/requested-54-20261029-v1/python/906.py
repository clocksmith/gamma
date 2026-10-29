"""Original development candidate; independent qualification pending."""
from math import isqrt

def solve(left, right):
    lo,hi = int(left),int(right)
    limit = isqrt(hi)
    answer = 0
    prefix = 1
    while True:
        s = str(prefix)
        odd = int(s+s[-2::-1])
        even = int(s+s[::-1])
        if odd > limit:
            break
        for root in (odd,even):
            square = root*root
            if lo <= square <= hi and str(square) == str(square)[::-1]:
                answer += 1
        prefix += 1
    return answer


class Solution:
    def superpalindromesInRange(self, left, right):
        return solve(left, right)
