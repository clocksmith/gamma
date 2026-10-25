class Solution:
    def maxAbsValExpr(self, arr1: list[int], arr2: list[int]) -> int:
        best = 0
        for first_sign in (-1, 1):
            for second_sign in (-1, 1):
                lowest = first_sign * arr1[0] + second_sign * arr2[0]
                highest = lowest
                for index in range(1, len(arr1)):
                    value = first_sign * arr1[index] + second_sign * arr2[index] + index
                    lowest = min(lowest, value)
                    highest = max(highest, value)
                best = max(best, highest - lowest)
        return best
