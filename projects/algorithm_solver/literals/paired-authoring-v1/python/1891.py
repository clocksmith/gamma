class Solution:
    def maxLength(self, ribbons, k):
        low = 0
        high = max(ribbons, default=0)
        while low < high:
            length = low + (high - low + 1) // 2
            pieces = 0
            for ribbon in ribbons:
                pieces += ribbon // length
                if pieces >= k:
                    break
            if pieces >= k:
                low = length
            else:
                high = length - 1
        return low
