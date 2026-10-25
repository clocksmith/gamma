class Solution:
    def fixedPoint(self, values):
        low = 0
        high = len(values)
        while low < high:
            middle = low + (high - low) // 2
            if values[middle] < middle:
                low = middle + 1
            else:
                high = middle
        if low < len(values) and values[low] == low:
            return low
        return -1
