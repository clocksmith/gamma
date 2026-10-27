from bisect import bisect_right


def solve(nums):
    # Minimum increasing-chain cover equals longest non-increasing subsequence.
    tails = []
    for value in nums:
        value = -value
        position = bisect_right(tails, value)
        if position == len(tails):
            tails.append(value)
        else:
            tails[position] = value
    return len(tails)
