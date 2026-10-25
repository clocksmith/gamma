class Solution:
    def relativeSortArray(self, arr1: list[int], arr2: list[int]) -> list[int]:
        counts = [0] * 1001
        for value in arr1:
            counts[value] += 1
        result = []
        for value in arr2:
            while counts[value] > 0:
                result.append(value)
                counts[value] -= 1
        for value in range(1001):
            while counts[value] > 0:
                result.append(value)
                counts[value] -= 1
        return result
