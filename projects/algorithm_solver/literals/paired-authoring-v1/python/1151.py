class Solution:
    def minSwaps(self, data: list[int]) -> int:
        width = sum(data)
        if width <= 1:
            return 0
        ones = 0
        best = 0
        for index, value in enumerate(data):
            ones += value
            if index >= width:
                ones -= data[index - width]
            if index + 1 >= width:
                best = max(best, ones)
        return width - best
