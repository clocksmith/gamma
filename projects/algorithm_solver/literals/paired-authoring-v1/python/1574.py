class Solution:
    def findLengthOfShortestSubarray(self, arr: list[int]) -> int:
        size = len(arr)
        if size <= 1:
            return 0
        left = 0
        while left + 1 < size and arr[left] <= arr[left + 1]:
            left += 1
        if left == size - 1:
            return 0
        right = size - 1
        while right > 0 and arr[right - 1] <= arr[right]:
            right -= 1
        best = min(size - left - 1, right)
        first = 0
        second = right
        while first <= left and second < size:
            if arr[first] <= arr[second]:
                best = min(best, second - first - 1)
                first += 1
            else:
                second += 1
        return best
