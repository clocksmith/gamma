from collections import deque


def solve(nums, k):
    zero = [0]
    one = [0]
    count = [0]
    def add(x, delta):
        node = 0
        count[0] += delta
        for bit in range(14, -1, -1):
            branch = one if x >> bit & 1 else zero
            if branch[node] == 0:
                branch[node] = len(count)
                zero.append(0)
                one.append(0)
                count.append(0)
            node = branch[node]
            count[node] += delta
    def maximum(x):
        node = value = 0
        for bit in range(14, -1, -1):
            opposite = zero[node] if x >> bit & 1 else one[node]
            if opposite and count[opposite] > 0:
                value |= 1 << bit
                node = opposite
            else:
                node = one[node] if x >> bit & 1 else zero[node]
        return value
    prefix = [0]
    high = deque()
    low = deque()
    left = answer = 0
    for r, x in enumerate(nums):
        add(prefix[r], 1)
        prefix.append(prefix[-1] ^ x)
        while high and nums[high[-1]] <= x:
            high.pop()
        while low and nums[low[-1]] >= x:
            low.pop()
        high.append(r)
        low.append(r)
        while nums[high[0]] - nums[low[0]] > k:
            add(prefix[left], -1)
            if high[0] == left:
                high.popleft()
            if low[0] == left:
                low.popleft()
            left += 1
        answer = max(answer, maximum(prefix[-1]))
    return answer


class Solution:
    def maxXor(self, nums, k):
        return solve(nums, k)
