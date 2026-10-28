def solve(nums, target):
    n = len(nums)
    tree = [0] * (2 * n + 3)
    def add(i):
        while i < len(tree):
            tree[i] += 1
            i += i & -i
    def query(i):
        total = 0
        while i:
            total += tree[i]
            i -= i & -i
        return total
    prefix = 0
    answer = 0
    add(n + 1)
    for x in nums:
        prefix += 1 if x == target else -1
        index = prefix + n + 1
        answer += query(index - 1)
        add(index)
    return answer


class Solution:
    def countMajoritySubarrays(self, nums, target):
        return solve(nums, target)
