/**
 * 3792. Sum of Increasing Product Blocks
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(n).
 * Algorithm: Form successive products of blocks of lengths 1 through n, reducing after each multiplication.
 * Complexity: O(n^2) time; O(1) space.
 * Numeric semantics: Reduced products < 1000000007 multiply a factor <= 500500, so every intermediate integer is below 2^53; returned residue is Number/int.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/sum-of-increasing-product-blocks/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3792.Sum%20of%20Increasing%20Product%20Blocks/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 */

function solve(n) {
  const modulus = 1000000007;
  let nextFactor = 1;
  let total = 0;
  for (let length = 1; length <= n; length += 1) {
    let product = 1;
    for (let factor = nextFactor; factor < nextFactor + length; factor += 1) {
      product = (product * factor) % modulus;
    }
    total = (total + product) % modulus;
    nextFactor += length;
  }
  return total;
}

function sumOfBlocks(n) {
  return solve(n);
}

class Solution {
  sumOfBlocks(n) {
    return solve(n);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, sumOfBlocks, Solution };
}
