"""Hack2Hire 67886e3c402dc47b67a14940 (Windowed Average excluding Largest K) over an INFERRED spec; qualification unknown."""

import heapq


def solve(nums, windowSize, k):
    w = windowSize
    top, rest = [], []  # top: min-heap of (value, index); rest: max-heap of (-value, -index)
    where = [0] * len(nums)  # 1 = in top, 2 = in rest, 0 = gone
    state = {'top_size': 0, 'top_sum': 0, 'rest_size': 0}
    left = 0
    window_sum = 0
    out = []

    def clean_top():
        while top and (top[0][1] < left or where[top[0][1]] != 1):
            heapq.heappop(top)

    def clean_rest():
        while rest and (-rest[0][1] < left or where[-rest[0][1]] != 2):
            heapq.heappop(rest)

    for i, v in enumerate(nums):
        if i >= w:
            j = i - w
            left = j + 1
            window_sum -= nums[j]
            if where[j] == 1:
                state['top_size'] -= 1
                state['top_sum'] -= nums[j]
            else:
                state['rest_size'] -= 1
            where[j] = 0
        window_sum += v
        heapq.heappush(top, (v, i))
        where[i] = 1
        state['top_size'] += 1
        state['top_sum'] += v
        clean_top()
        x, xi = heapq.heappop(top)  # move the smallest of top to rest
        where[xi] = 2
        state['top_size'] -= 1
        state['top_sum'] -= x
        state['rest_size'] += 1
        heapq.heappush(rest, (-x, -xi))
        while state['top_size'] < k and state['rest_size'] > 0:
            clean_rest()
            nx, nxi = heapq.heappop(rest)
            where[-nxi] = 1
            state['rest_size'] -= 1
            state['top_size'] += 1
            state['top_sum'] -= nx
            heapq.heappush(top, (-nx, -nxi))
        if i >= w - 1:
            out.append((window_sum - state['top_sum']) // (w - k))
    return out


class Solution:
    def windowAverages(self, nums, windowSize, k):
        return solve(nums, windowSize, k)
