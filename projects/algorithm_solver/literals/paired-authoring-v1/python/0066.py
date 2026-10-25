class Solution:
    def plusOne(self, digits: list[int]) -> list[int]:
        result = digits.copy()
        for index in range(len(result) - 1, -1, -1):
            if result[index] < 9:
                result[index] += 1
                return result
            result[index] = 0
        return [1] + result
