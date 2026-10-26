"""3321. Find X-Sum of All K-Long Subarrays II.

Compress all reachable (frequency,value) ranks and maintain order counts and weighted sums in Fenwick trees; O(n log n) time and O(n) space. Inputs are preserved.
"""

from collections import Counter


def solve(nums: list[int], k: int, x: int) -> list[int]:
    totals = Counter(nums)
    pairs = sorted((count, value) for value, maximum in totals.items() for count in range(1, maximum + 1))
    ranks = {value: [0] * (maximum + 1) for value, maximum in totals.items()}
    for rank, (count, value) in enumerate(pairs, 1):
        ranks[value][count] = rank
    size = len(pairs)
    counts, sums = [0] * (size + 1), [0] * (size + 1)
    frequency = Counter()
    active = total = 0

    def update(rank, difference, weight):
        while rank <= size:
            counts[rank] += difference
            sums[rank] += weight
            rank += rank & -rank

    def change(value, difference):
        nonlocal active, total
        before = frequency[value]
        if before:
            update(ranks[value][before], -1, -before * value)
            active -= 1
        after = before + difference
        frequency[value] = after
        if after:
            update(ranks[value][after], 1, after * value)
            active += 1
        total += difference * value

    def smallest_sum(amount):
        index = answer = 0
        step = 1 << (size.bit_length() - 1)
        while step:
            following = index + step
            if following <= size and counts[following] <= amount:
                amount -= counts[following]
                answer += sums[following]
                index = following
            step >>= 1
        return answer

    answers = []
    for index, value in enumerate(nums):
        change(value, 1)
        if index >= k:
            change(nums[index - k], -1)
        if index + 1 >= k:
            answers.append(total - smallest_sum(max(0, active - x)))
    return answers


class Solution:
    def findXSum(self, nums: list[int], k: int, x: int) -> list[int]:
        return solve(nums, k, x)
