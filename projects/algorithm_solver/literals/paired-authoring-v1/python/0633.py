def floor_sqrt(value: int) -> int:
    lower = 0
    # Largest root whose square is a safe integer in both languages.
    upper = min(value, 94906265) + 1
    while lower < upper:
        middle = lower + (upper - lower) // 2
        if middle * middle <= value:
            lower = middle + 1
        else:
            upper = middle
    return lower - 1


class Solution:
    def judgeSquareSum(self, c: int) -> bool:
        left = 0
        right = floor_sqrt(c)
        while left <= right:
            total = left * left + right * right
            if total == c:
                return True
            if total < c:
                left += 1
            else:
                right -= 1
        return False
