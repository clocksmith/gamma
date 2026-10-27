/**
 * 3730. Maximum Calories Burnt from Jumps
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(heights).
 * Algorithm: Sort and visit alternating largest/smallest unused heights, beginning at ground zero.
 * Complexity: O(n log n) time; O(n) space.
 * Numeric semantics: All squared differences and the sum (at most 10^15) are exact JavaScript Number integers; Python uses int.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/maximum-calories-burnt-from-jumps/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3730.Maximum%20Calories%20Burnt%20from%20Jumps/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 * Contract note: No final return to ground is added.
 */

function solve(heights) {
  const ordered = heights.slice().sort((a, b) => a - b);
  let left = 0;
  let right = ordered.length - 1;
  let previous = 0;
  let total = 0;
  let takeLargest = true;
  while (left <= right) {
    const current = takeLargest ? ordered[right--] : ordered[left++];
    const difference = current - previous;
    total += difference * difference;
    previous = current;
    takeLargest = !takeLargest;
  }
  return total;
}

function maxCaloriesBurnt(heights) {
  return solve(heights);
}

class Solution {
  maxCaloriesBurnt(heights) {
    return solve(heights);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, maxCaloriesBurnt, Solution };
}
