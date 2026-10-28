"""Original frontend 3800 development variant; qualification unknown."""

def solve(s, t, flipCost, swapCost, crossCost):
    a = b = 0
    for first, second in zip(s, t):
        if first != second:
            if first == '0':
                a += 1
            else:
                b += 1
    paired = min(a, b)
    remaining = abs(a - b)
    return paired * min(swapCost, 2 * flipCost) + (remaining // 2) * min(crossCost + swapCost, 2 * flipCost) + (remaining % 2) * flipCost


class Solution:
    def minimumCost(self, s, t, flipCost, swapCost, crossCost):
        return solve(s, t, flipCost, swapCost, crossCost)
