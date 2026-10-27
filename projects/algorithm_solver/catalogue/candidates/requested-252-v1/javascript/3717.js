/**
 * 3717. Minimum Operations to Make the Array Beautiful
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(nums).
 * Algorithm: Dynamic programming over last written value, transitioning to allowed multiples.
 * Complexity: O(n M log M) time and O(M) space, M=max(nums) <= 50.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/minimum-operations-to-make-the-array-beautiful/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3717.Minimum%20Operations%20to%20Make%20the%20Array%20Beautiful/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 * Contract note: Cap 2M is sufficient: at the first value reaching M, replace it by the least multiple of its predecessor >= M (<2M), then keep the whole suffix at that value. This never costs more than a chain exceeding 2M.
 */

function solve(nums) {
  let maximum = 0;
  for (const value of nums) maximum = Math.max(maximum, value);
  const cap = 2 * maximum;
  let costs = new Array(cap + 1).fill(Infinity);
  costs[nums[0]] = 0;
  for (let index = 1; index < nums.length; index += 1) {
    const original = nums[index];
    const nextCosts = new Array(cap + 1).fill(Infinity);
    for (let previous = 1; previous <= cap; previous += 1) {
      if (costs[previous] === Infinity) continue;
      const first = Math.ceil(original / previous) * previous;
      for (let current = first; current <= cap; current += previous) {
        nextCosts[current] = Math.min(nextCosts[current], costs[previous] + current - original);
      }
    }
    costs = nextCosts;
  }
  return Math.min(...costs);
}

function minOperations(nums) {
  return solve(nums);
}

class Solution {
  minOperations(nums) {
    return solve(nums);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, minOperations, Solution };
}
