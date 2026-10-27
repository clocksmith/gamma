"""3792. Sum of Increasing Product Blocks
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(n).
Algorithm: Form successive products of blocks of lengths 1 through n, reducing after each multiplication.
Complexity: O(n^2) time; O(1) space.
Numeric semantics: Reduced products < 1000000007 multiply a factor <= 500500, so every intermediate integer is below 2^53; returned residue is Number/int.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/sum-of-increasing-product-blocks/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3792.Sum%20of%20Increasing%20Product%20Blocks/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
"""

def solve(n):
    modulus = 1_000_000_007
    next_factor = 1
    total = 0
    for length in range(1, n + 1):
        product = 1
        for factor in range(next_factor, next_factor + length):
            product = product * factor % modulus
        total = (total + product) % modulus
        next_factor += length
    return total


def sumOfBlocks(n):
    return solve(n)


class Solution:
    def sumOfBlocks(self, n):
        return solve(n)
