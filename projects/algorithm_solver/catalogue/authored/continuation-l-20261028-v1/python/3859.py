"""Original frontend 3859 variant; qualification unknown."""

def solve(nums, k, m):
    values = {value: i for i, value in enumerate(set(nums))}
    size = 1
    while size < len(values):
        size *= 2
    infinity = len(nums) + 1
    tree = [infinity] * (2 * size)
    def update(index, value):
        node = size + index
        tree[node] = value
        node //= 2
        while node:
            tree[node] = min(tree[node * 2], tree[node * 2 + 1])
            node //= 2
    positions = [[] for _ in values]
    counts = [0] * len(values)
    left = distinct = answer = 0
    for right, value in enumerate(nums):
        index = values[value]
        positions[index].append(right)
        if counts[index] == 0:
            distinct += 1
        counts[index] += 1
        update(index, positions[index][-m] if len(positions[index]) >= m else -1)
        while distinct > k:
            outgoing = values[nums[left]]
            counts[outgoing] -= 1
            if counts[outgoing] == 0:
                distinct -= 1
                update(outgoing, infinity)
            left += 1
        if distinct == k:
            answer += max(0, tree[1] - left + 1)
    return answer


class Solution:
    def countSubarrays(self, nums, k, m):
        return solve(nums, k, m)
