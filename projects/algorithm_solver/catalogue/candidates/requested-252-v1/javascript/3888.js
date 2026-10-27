/**
 * 3888. Minimum Operations to Make All Grid Elements Equal
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(grid, k).
 * Algorithm: Symbolic row-major 2D difference sweep: every forced k-square count is affine in target T; intersect nonnegativity inequalities and edge equalities, choose least feasible T.
 * Complexity: O(m*n) arithmetic operations and O(m*n) space; exact integer arithmetic.
 * Numeric semantics: JavaScript returns BigInt (including -1n); Python int. solveJson returns decimal strings. Affine per-cell constants are integer sums bounded by O(m*n*maxAbsGrid) and stored exactly in Float64; aggregate counts use BigInt.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: solve(grid, k), minOperations, Solution.minOperations; solveJson explicit JSON transport. Gamma BigInt result binding pending.
 * Specification: https://leetcode.com/problems/minimum-operations-to-make-all-grid-elements-equal/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3888.Minimum%20Operations%20to%20Make%20All%20Grid%20Elements%20Equal/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 * Contract note: Does not assume the target is max(grid) or max(grid)+1. An anchor at each legal cell is forced by prior coverage; boundary residuals constrain the same target. Total operations = (m*n*T-sum(grid))/(k*k), hence smallest feasible T minimizes work.
 */

function solve(grid, k) {
  const rows = grid.length;
  const columns = grid[0].length;
  const stride = columns + 1;
  const coefficients = new Float64Array((rows + 1) * stride);
  const constants = new Float64Array((rows + 1) * stride);
  let lower = -Infinity;
  for (const row of grid) for (const value of row) lower = Math.max(lower, value);
  let upper = Infinity;
  let totalCoefficient = 0n;
  let totalConstant = 0n;
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      const position = row * stride + column;
      let coefficient = coefficients[position];
      let constant = constants[position];
      if (row > 0) {
        coefficient += coefficients[position - stride];
        constant += constants[position - stride];
      }
      if (column > 0) {
        coefficient += coefficients[position - 1];
        constant += constants[position - 1];
      }
      if (row > 0 && column > 0) {
        coefficient -= coefficients[position - stride - 1];
        constant -= constants[position - stride - 1];
      }
      coefficients[position] = coefficient;
      constants[position] = constant;
      const neededCoefficient = 1 - coefficient;
      const neededConstant = -grid[row][column] - constant;
      if (row + k <= rows && column + k <= columns) {
        // Forced anchor count a*T+b must be a nonnegative integer.
        if (neededCoefficient > 0) lower = Math.max(lower, Math.ceil(-neededConstant / neededCoefficient));
        else if (neededCoefficient < 0) upper = Math.min(upper, Math.floor(-neededConstant / neededCoefficient));
        else if (neededConstant < 0) return -1n;
        totalCoefficient += BigInt(neededCoefficient);
        totalConstant += BigInt(neededConstant);
        coefficients[position] += neededCoefficient;
        constants[position] += neededConstant;
        const below = (row + k) * stride + column;
        const right = row * stride + column + k;
        const corner = (row + k) * stride + column + k;
        coefficients[below] -= neededCoefficient;
        constants[below] -= neededConstant;
        coefficients[right] -= neededCoefficient;
        constants[right] -= neededConstant;
        coefficients[corner] += neededCoefficient;
        constants[corner] += neededConstant;
      } else {
        if (neededCoefficient === 0) {
          if (neededConstant !== 0) return -1n;
        } else {
          const numerator = -neededConstant;
          if (numerator % neededCoefficient !== 0) return -1n;
          const required = numerator / neededCoefficient;
          lower = Math.max(lower, required);
          upper = Math.min(upper, required);
        }
      }
      if (lower > upper) return -1n;
    }
  }
  return totalCoefficient * BigInt(lower) + totalConstant;
}

function solveJson(grid, k) {
  return solve(grid, k).toString();
}

function minOperations(grid, k) {
  return solve(grid, k);
}

class Solution {
  minOperations(grid, k) {
    return solve(grid, k);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, solveJson, minOperations, Solution };
}
