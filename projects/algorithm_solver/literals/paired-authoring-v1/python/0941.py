class Solution:
    def validMountainArray(self, arr: list[int]) -> bool:
        if len(arr) < 3:
            return False

        index = 0
        while index + 1 < len(arr) and arr[index] < arr[index + 1]:
            index += 1
        if index == 0 or index == len(arr) - 1:
            return False
        while index + 1 < len(arr) and arr[index] > arr[index + 1]:
            index += 1
        return index == len(arr) - 1
