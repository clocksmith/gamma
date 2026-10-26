"""860. Lemonade Change (Easy).

Specification: https://leetcode.com/problems/lemonade-change/description/
"""


def solve(bills: list[int]) -> bool:
    """O(n) time, O(1) space; prefer one ten and one five when changing a twenty."""
    fives = tens = 0
    for bill in bills:
        if bill == 5:
            fives += 1
        elif bill == 10:
            if fives == 0:
                return False
            fives -= 1
            tens += 1
        elif tens > 0 and fives > 0:
            tens -= 1
            fives -= 1
        elif fives >= 3:
            fives -= 3
        else:
            return False
    return True


class Solution:
    def lemonadeChange(self, bills: list[int]) -> bool:
        return solve(bills)
