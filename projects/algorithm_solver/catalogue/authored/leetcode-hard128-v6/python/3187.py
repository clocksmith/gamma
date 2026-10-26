"""3187. Peaks in Array.

Fenwick sums over peak indicators; each update affects at most three indicators. O((n+q) log n) time, O(n) space. Inputs are preserved.
"""

def solve(nums: list[int], queries: list[list[int]]) -> list[int]:
    values = nums[:]
    n = len(values)
    tree = [0] * (n + 1)

    def peak(index):
        return 0 < index < n - 1 and values[index] > values[index - 1] and values[index] > values[index + 1]

    def add(index, change):
        index += 1
        while index <= n:
            tree[index] += change
            index += index & -index

    def prefix(end):
        total = 0
        while end:
            total += tree[end]
            end -= end & -end
        return total

    for index in range(1, n - 1):
        if peak(index):
            add(index, 1)
    answer = []
    for kind, first, second in queries:
        if kind == 1:
            answer.append(prefix(second) - prefix(first + 1) if second - first > 1 else 0)
        else:
            affected = [(index, int(peak(index))) for index in range(max(1, first - 1), min(n - 2, first + 1) + 1)]
            values[first] = second
            for index, old in affected:
                add(index, int(peak(index)) - old)
    return answer


class Solution:
    def countOfPeaks(self, nums: list[int], queries: list[list[int]]) -> list[int]:
        return solve(nums, queries)
