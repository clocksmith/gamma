class Solution:
    def prevPermOpt1(self, arr: list[int]) -> list[int]:
        pivot = len(arr) - 2
        while pivot >= 0 and arr[pivot] <= arr[pivot + 1]:
            pivot -= 1
        if pivot < 0:
            return arr
        replacement = len(arr) - 1
        while arr[replacement] >= arr[pivot]:
            replacement -= 1
        while replacement > pivot + 1 and arr[replacement - 1] == arr[replacement]:
            replacement -= 1
        arr[pivot], arr[replacement] = arr[replacement], arr[pivot]
        return arr
