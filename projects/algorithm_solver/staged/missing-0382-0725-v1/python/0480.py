"""480. Sliding Window Median. Coordinate-compressed frequency tree; O(n log n) time and O(n) space."""

class _Fenwick:
    def __init__(self, n):
        self.tree = [0] * (n + 1)

    def add(self, i, delta):
        while i < len(self.tree):
            self.tree[i] += delta
            i += i & -i

    def prefix(self, i):
        total = 0
        while i:
            total += self.tree[i]
            i -= i & -i
        return total

def solve(nums: list[int], k: int) -> list[float]:
    values = sorted(set(nums))
    ranks = {value: i + 1 for i, value in enumerate(values)}
    tree = _Fenwick(len(values))
    def select(order):
        index = 0
        step = 1 << (len(values).bit_length() - 1)
        while step:
            candidate = index + step
            if candidate < len(tree.tree) and tree.tree[candidate] < order:
                index = candidate
                order -= tree.tree[candidate]
            step >>= 1
        return values[index]
    answer = []
    for i, value in enumerate(nums):
        tree.add(ranks[value], 1)
        if i >= k:
            tree.add(ranks[nums[i - k]], -1)
        if i + 1 >= k:
            if k % 2:
                answer.append(float(select(k // 2 + 1)))
            else:
                answer.append((select(k // 2) + select(k // 2 + 1)) / 2)
    return answer


class Solution:
    def medianSlidingWindow(self, nums: list[int], k: int) -> list[float]:
        return solve(nums, k)
