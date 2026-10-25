def upper_bound(values: list[int], target: int) -> int:
    left = 0
    right = len(values)
    while left < right:
        middle = left + (right - left) // 2
        if values[middle] <= target:
            left = middle + 1
        else:
            right = middle
    return left


class Solution:
    def maxTwoEvents(self, events: list[list[int]]) -> int:
        ordered = sorted(events, key=lambda event: event[0])
        starts = [event[0] for event in ordered]
        suffix = [0] * (len(ordered) + 1)
        for index in range(len(ordered) - 1, -1, -1):
            suffix[index] = max(suffix[index + 1], ordered[index][2])
        best = 0
        for start, end, value in ordered:
            following = upper_bound(starts, end)
            best = max(best, value + suffix[following])
        return best
