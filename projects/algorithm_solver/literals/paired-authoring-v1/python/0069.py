class Solution:
    def mySqrt(self, x: int) -> int:
        lower = 0
        # Largest root whose square is a safe integer in both languages.
        upper = min(x, 94906265) + 1
        while lower < upper:
            middle = lower + (upper - lower) // 2
            if middle * middle <= x:
                lower = middle + 1
            else:
                upper = middle
        return lower - 1
