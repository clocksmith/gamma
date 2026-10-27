"""3888. Minimum Operations to Make All Grid Elements Equal
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(grid, k).
Algorithm: Symbolic row-major 2D difference sweep: every forced k-square count is affine in target T; intersect nonnegativity inequalities and edge equalities, choose least feasible T.
Complexity: O(m*n) arithmetic operations and O(m*n) space; exact integer arithmetic.
Numeric semantics: JavaScript returns BigInt (including -1n); Python int. solveJson returns decimal strings. Affine per-cell constants are integer sums bounded by O(m*n*maxAbsGrid) and stored exactly in Float64; aggregate counts use BigInt.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: solve(grid, k), minOperations, Solution.minOperations; solveJson explicit JSON transport. Gamma BigInt result binding pending.
Specification: https://leetcode.com/problems/minimum-operations-to-make-all-grid-elements-equal/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3888.Minimum%20Operations%20to%20Make%20All%20Grid%20Elements%20Equal/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: Does not assume the target is max(grid) or max(grid)+1. An anchor at each legal cell is forced by prior coverage; boundary residuals constrain the same target. Total operations = (m*n*T-sum(grid))/(k*k), hence smallest feasible T minimizes work.
"""

def solve(grid, k):
    rows, columns = len(grid), len(grid[0])
    stride = columns + 1
    coefficients = [0] * ((rows + 1) * stride)
    constants = [0] * ((rows + 1) * stride)
    lower = max(max(row) for row in grid)
    upper = None
    total_coefficient = 0
    total_constant = 0
    for row in range(rows):
        for column in range(columns):
            position = row * stride + column
            coefficient = coefficients[position]
            constant = constants[position]
            if row:
                coefficient += coefficients[position - stride]
                constant += constants[position - stride]
            if column:
                coefficient += coefficients[position - 1]
                constant += constants[position - 1]
            if row and column:
                coefficient -= coefficients[position - stride - 1]
                constant -= constants[position - stride - 1]
            coefficients[position] = coefficient
            constants[position] = constant
            needed_coefficient = 1 - coefficient
            needed_constant = -grid[row][column] - constant
            if row + k <= rows and column + k <= columns:
                # The forced count at this anchor is a*T+b and must be >= 0.
                if needed_coefficient > 0:
                    lower = max(lower, -(needed_constant // needed_coefficient))
                elif needed_coefficient < 0:
                    bound = (-needed_constant) // needed_coefficient
                    upper = bound if upper is None else min(upper, bound)
                elif needed_constant < 0:
                    return -1
                total_coefficient += needed_coefficient
                total_constant += needed_constant
                coefficients[position] += needed_coefficient
                constants[position] += needed_constant
                below = (row + k) * stride + column
                right = row * stride + column + k
                corner = (row + k) * stride + column + k
                coefficients[below] -= needed_coefficient
                constants[below] -= needed_constant
                coefficients[right] -= needed_coefficient
                constants[right] -= needed_constant
                coefficients[corner] += needed_coefficient
                constants[corner] += needed_constant
            else:
                # No future anchor can change this cell; its residual must be zero.
                if needed_coefficient == 0:
                    if needed_constant != 0:
                        return -1
                else:
                    numerator = -needed_constant
                    if numerator % needed_coefficient:
                        return -1
                    required = numerator // needed_coefficient
                    lower = max(lower, required)
                    upper = required if upper is None else min(upper, required)
            if upper is not None and lower > upper:
                return -1
    return total_coefficient * lower + total_constant


def solveJson(grid, k):
    return str(solve(grid, k))


def minOperations(grid, k):
    return solve(grid, k)


class Solution:
    def minOperations(self, grid, k):
        return solve(grid, k)
