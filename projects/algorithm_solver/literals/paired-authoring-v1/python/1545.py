class Solution:
    def findKthBit(self, n: int, k: int) -> str:
        inverted = False
        while n > 1:
            middle = 2 ** (n - 1)
            if k == middle:
                return "0" if inverted else "1"
            if k > middle:
                k = 2 * middle - k
                inverted = not inverted
            n -= 1
        return "1" if inverted else "0"
