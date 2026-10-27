"""3704. Count No-Zero Pairs That Sum to N
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-no-zero-pairs-that-sum-to-n/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3704.Count%20No-Zero%20Pairs%20That%20Sum%20to%20N/README_EN.md
Complexity: O(log n) states with a constant 100 digit-pair factor; O(log n) digit storage.
Ordered positive pairs. JavaScript BigInt counts internally; answer <= n-1 <= 1e15 converts exactly to Number.
"""

from __future__ import annotations

def solve(n):
    digits = [int(character) for character in reversed(str(n))] + [0]
    states = {(0, False, False): 1}
    for position, target in enumerate(digits):
        following = {}
        for (carry, ended_a, ended_b), ways in states.items():
            choices_a = [0] if ended_a else range(1 if position == 0 else 0, 10)
            choices_b = [0] if ended_b else range(1 if position == 0 else 0, 10)
            for digit_a in choices_a:
                for digit_b in choices_b:
                    total = carry + digit_a + digit_b
                    if total % 10 == target:
                        key = (total // 10, ended_a or digit_a == 0, ended_b or digit_b == 0)
                        following[key] = following.get(key, 0) + ways
        states = following
    return states.get((0, True, True), 0)


class Solution:
    def countNoZeroPairs(self, n):
        return solve(n)
