/**
 * 3837. Delayed Count of Equal Elements
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(nums, k).
 * Algorithm: Grow a suffix frequency map while scanning indices backward.
 * Complexity: O(n) expected time; O(n) space.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/delayed-count-of-equal-elements/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3837.Delayed%20Count%20of%20Equal%20Elements/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 * Contract note: The inequality is strict: j > i + k.
 */

function solve(nums, k) {
  const counts = new Map();
  const answer = new Array(nums.length).fill(0);
  for (let index = nums.length - k - 2; index >= 0; index -= 1) {
    const value = nums[index + k + 1];
    counts.set(value, (counts.get(value) || 0) + 1);
    answer[index] = counts.get(nums[index]) || 0;
  }
  return answer;
}

function delayedCount(nums, k) {
  return solve(nums, k);
}

class Solution {
  delayedCount(nums, k) {
    return solve(nums, k);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, delayedCount, Solution };
}
