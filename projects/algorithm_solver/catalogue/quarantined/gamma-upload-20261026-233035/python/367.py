"""367. Valid Perfect Square."""
def solve(num: int) -> bool:
    left, right = 0, num
    while left <= right:
        middle = (left + right) // 2
        square = middle * middle
        if square == num:
            return True
        if square < num:
            left = middle + 1
        else:
            right = middle - 1
    return False

class Solution:
    def isPerfectSquare(self, num: int) -> bool:
        return solve(num)
