/**
 * 3763. Maximum Total Sum with Threshold Constraints
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(nums, threshold).
 * Algorithm: Process indices in increasing eligibility threshold; the first gap is an unavoidable stopping point.
 * Complexity: O(n log n) time; O(n) space.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/maximum-total-sum-with-threshold-constraints/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3763.Maximum%20Total%20Sum%20with%20Threshold%20Constraints/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 * Contract note: All rewards are positive. If sorted threshold at position j exceeds j+1, only j items can be eligible then; no ordering passes that gap. Every earlier item can and must ultimately be consumed.
 */

function solve(nums, threshold) {
  const order = Array.from({ length: nums.length }, (_, index) => index);
  order.sort((left, right) => threshold[left] - threshold[right] || left - right);
  let total = 0;
  for (let position = 0; position < order.length; position += 1) {
    const index = order[position];
    if (threshold[index] > position + 1) break;
    total += nums[index];
  }
  return total;
}

function maxSum(nums, threshold) {
  return solve(nums, threshold);
}

class Solution {
  maxSum(nums, threshold) {
    return solve(nums, threshold);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, maxSum, Solution };
}
