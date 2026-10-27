"""3962. Maximum Subarray Sum After at Most K Swaps
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-subarray-sum-after-at-most-k-swaps/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3962.Maximum%20Subarray%20Sum%20After%20at%20Most%20K%20Swaps/README_EN.md
Complexity: O(n^2 log^2 n) time, O(n) space.
Exact interval enumeration with best improving inside/outside exchanges. n <= 1500. No candidate execution or maximum-size performance measurement. Inputs preserved; native method pending.
"""

from __future__ import annotations

class RankTree:
    def __init__(self, values):
        self.values = values
        self.counts = [0] * (len(values) + 1)
        self.sums = [0] * (len(values) + 1)
        self.size = 0
        self.total = 0

    def add(self, index, delta):
        value = self.values[index]
        self.size += delta
        self.total += delta * value
        index += 1
        while index < len(self.counts):
            self.counts[index] += delta
            self.sums[index] += delta * value
            index += index & -index

    def select(self, rank):
        index = 0
        total = 0
        bit = 1 << (len(self.values).bit_length() - 1)
        while bit:
            candidate = index + bit
            if candidate < len(self.counts) and self.counts[candidate] < rank:
                rank -= self.counts[candidate]
                total += self.sums[candidate]
                index = candidate
            bit >>= 1
        return self.values[index], total + rank * self.values[index]

    def smallest_sum(self, count):
        return self.select(count)[1] if count else 0


def solve(nums, k):
    n = len(nums)
    if k == 0:
        best = running = nums[0]
        for value in nums[1:]:
            running = max(value, running + value)
            best = max(best, running)
        return best
    positives = [value for value in nums if value > 0]
    if not positives:
        return max(nums)
    if k >= min(len(positives), n - len(positives)):
        return sum(positives)
    values = sorted(set(nums))
    indices = {value: index for index, value in enumerate(values)}
    answer = max(nums)
    for left in range(n):
        inside = RankTree(values)
        outside = RankTree(values)
        for value in nums:
            outside.add(indices[value], 1)
        current = 0
        for right in range(left, n):
            value = nums[right]
            inside.add(indices[value], 1)
            outside.add(indices[value], -1)
            current += value
            low, high = 0, min(k, inside.size, outside.size)
            while low < high:
                middle = (low + high + 1) // 2
                if inside.select(middle)[0] < outside.select(outside.size - middle + 1)[0]:
                    low = middle
                else:
                    high = middle - 1
            gain = outside.total - outside.smallest_sum(outside.size - low) - inside.smallest_sum(low)
            answer = max(answer, current + gain)
    return answer
