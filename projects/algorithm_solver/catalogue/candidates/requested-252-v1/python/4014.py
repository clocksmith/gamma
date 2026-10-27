"""4014. Minimum Total Price After Applying Discounts
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-total-price-after-applying-discounts/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4014.Minimum%20Total%20Price%20After%20Applying%20Discounts/README_EN.md
Complexity: O(n log n + m log m) time, O(n+m) space.
Match largest discounts to largest prices. Accumulate exact integer hundredths; perform one final division without per-item rounding. Inputs preserved.
"""

from __future__ import annotations

def solve(prices, discounts):
    ordered = sorted(prices, reverse=True)
    offers = sorted(discounts, reverse=True)
    hundredths = sum(ordered) * 100
    for price, discount in zip(ordered, offers):
        hundredths -= price * discount
    return hundredths / 100


class Solution:
    def minPrice(self, prices, discounts):
        return solve(prices, discounts)
