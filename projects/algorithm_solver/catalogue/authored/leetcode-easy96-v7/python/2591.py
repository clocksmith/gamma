"""2591. Distribute Money to Maximum Children (Easy).

Specification: https://leetcode.com/problems/distribute-money-to-maximum-children/description/
"""


def solve(money: int, children: int) -> int:
    """O(1) time and space; reserve one dollar each, maximize eights, and repair leftover/four-dollar cases."""
    if money < children:
        return -1
    extra = money - children
    eights = min(children, extra // 7)
    extra -= eights * 7
    if eights == children and extra > 0:
        eights -= 1
    elif eights == children - 1 and extra == 3:
        eights -= 1
    return eights


class Solution:
    def distMoney(self, money: int, children: int) -> int:
        return solve(money, children)
