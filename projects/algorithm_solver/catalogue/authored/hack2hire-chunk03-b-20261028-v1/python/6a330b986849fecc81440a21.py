"""Hack2Hire 6a330b986849fecc81440a21 (Minimum Variant Conversion) over an INFERRED spec; qualification unknown."""


def solve(product, k):
    ones = sum(product)
    if ones == 0: return 0
    window = sum(product[:k])
    smallest = window if window > 0 else ones
    for i in range(k, len(product)):
        window += product[i] - product[i - k]
        if 0 < window < smallest: smallest = window
    return ones + smallest * (smallest - 1) // 2


class Solution:
    def minimumConversionCost(self, product, k):
        return solve(product, k)
