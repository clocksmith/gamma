"""2121. Intervals Between Identical Elements: accumulate equal-value index distances from both directions."""


def solve(arr: list[int]) -> list[int]:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    answer = [0] * len(arr)
    counts, totals = {}, {}
    for index, value in enumerate(arr):
        count, total = counts.get(value, 0), totals.get(value, 0)
        answer[index] = index * count - total
        counts[value] = count + 1
        totals[value] = total + index
    counts, totals = {}, {}
    for index in range(len(arr) - 1, -1, -1):
        value = arr[index]
        count, total = counts.get(value, 0), totals.get(value, 0)
        answer[index] += total - index * count
        counts[value] = count + 1
        totals[value] = total + index
    return answer


class Solution:
    def getDistances(self, arr: list[int]) -> list[int]:
        return solve(arr)
