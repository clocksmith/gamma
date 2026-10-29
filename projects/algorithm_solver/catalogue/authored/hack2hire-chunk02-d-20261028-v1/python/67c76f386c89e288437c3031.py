"""Hack2Hire 67c76f386c89e288437c3031 (Fill Equation with Operators) over an INFERRED spec; qualification unknown."""


def solve(equation):
    left, target = equation.split(' = ')
    nums = [int(x) for x in left.split(' ')]
    goal = int(target)
    n = len(nums)
    memo = {}

    def forms(i, j):
        # (sums, products) for nums[i..j]: lists of (text, value); atoms count as products of one factor.
        key = (i, j)
        if key in memo:
            return memo[key]
        if i == j:
            memo[key] = ([], [(str(nums[i]), nums[i])])
            return memo[key]
        sums, products = [], []
        # Sum = first part (non-sum) + rest (sum or non-sum), split at first top-level '+'.
        for k in range(i, j):
            head_parts = forms(i, k)[1]
            tail_sums, tail_products = forms(k + 1, j)
            for ht, hv in head_parts:
                for tt, tv in tail_sums:
                    sums.append((ht + '+' + tt, hv + tv))
                for tt, tv in tail_products:
                    sums.append((ht + '+' + tt, hv + tv))
        # Product = first factor (atom or parenthesised sum) * rest (product or factor).
        for k in range(i, j):
            factors = [('(' + t + ')', v) for t, v in forms(i, k)[0]]
            if k == i:
                factors.append((str(nums[i]), nums[i]))
            tail_sums, tail_products = forms(k + 1, j)
            tails = [('(' + t + ')', v) for t, v in tail_sums] + tail_products
            for ft, fv in factors:
                for tt, tv in tails:
                    products.append((ft + '*' + tt, fv * tv))
        memo[key] = (sums, products)
        return memo[key]

    sums, products = forms(0, n - 1)
    return sorted({text for text, value in sums + products if value == goal})


class Solution:
    def fillOperators(self, equation):
        return solve(equation)
