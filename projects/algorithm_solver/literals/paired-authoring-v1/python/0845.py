class Solution:
    def longestMountain(self, arr: list[int]) -> int:
        uphill = 0
        downhill = 0
        longest = 0
        for index in range(1, len(arr)):
            previous = arr[index - 1]
            current = arr[index]
            if current == previous or (downhill > 0 and current > previous):
                uphill = 0
                downhill = 0
            if current > previous:
                uphill += 1
            elif current < previous and uphill > 0:
                downhill += 1
            if uphill > 0 and downhill > 0:
                longest = max(longest, uphill + downhill + 1)
        return longest
