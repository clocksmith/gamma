def greatest_common_divisor(left: int, right: int) -> int:
    while right != 0:
        left, right = right, left % right
    return left


class Solution:
    def hasGroupsSizeX(self, deck: list[int]) -> bool:
        if not deck:
            return False

        counts = {}
        for value in deck:
            counts[value] = counts.get(value, 0) + 1
        common = 0
        for count in counts.values():
            common = greatest_common_divisor(common, count)
            if common == 1:
                return False
        return common >= 2
