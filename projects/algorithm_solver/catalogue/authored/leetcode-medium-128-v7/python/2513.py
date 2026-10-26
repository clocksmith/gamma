"""2513. Minimize the Maximum of Two Arrays: binary search a bound satisfying both individual capacities and their union."""
from math import gcd


def solve(divisor1: int, divisor2: int, uniqueCnt1: int, uniqueCnt2: int) -> int:
    """O(log(divisor1 + divisor2) + log(uniqueCnt1 + uniqueCnt2)) time and O(1) auxiliary space; inputs are read-only."""
    common = divisor1 // gcd(divisor1, divisor2) * divisor2
    total = uniqueCnt1 + uniqueCnt2
    low, high = total, 2 * total
    while low < high:
        middle = (low + high) // 2
        feasible = (middle - middle // divisor1 >= uniqueCnt1
                    and middle - middle // divisor2 >= uniqueCnt2
                    and middle - middle // common >= total)
        if feasible:
            high = middle
        else:
            low = middle + 1
    return low


class Solution:
    def minimizeSet(self, divisor1: int, divisor2: int, uniqueCnt1: int, uniqueCnt2: int) -> int:
        return solve(divisor1, divisor2, uniqueCnt1, uniqueCnt2)
