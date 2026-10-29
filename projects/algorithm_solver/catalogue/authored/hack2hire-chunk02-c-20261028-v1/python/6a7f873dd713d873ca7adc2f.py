"""Hack2Hire 6a7f873dd713d873ca7adc2f (Balance Ads Across Columns, variant 1) over an INFERRED spec; qualification unknown."""

def solve(heights):
    left, right = [], []
    left_total = right_total = 0
    for index, height in enumerate(heights):
        if left_total <= right_total:
            left.append(index)
            left_total += height
        else:
            right.append(index)
            right_total += height
    return [left, right]


class Solution:
    def assignColumns(self, heights):
        return solve(heights)
