/**
 * 3817. Good Indices in a Digit String
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(s).
 * Algorithm: Compare each index decimal spelling with the substring ending there.
 * Complexity: O(n log n) character work; O(n) output space.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/good-indices-in-a-digit-string/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3817.Good%20Indices%20in%20a%20Digit%20String/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 */

function solve(s) {
  const result = [];
  for (let index = 0; index < s.length; index += 1) {
    const digits = String(index);
    const start = index + 1 - digits.length;
    if (start >= 0 && s.slice(start, index + 1) === digits) result.push(index);
  }
  return result;
}

function goodIndices(s) {
  return solve(s);
}

class Solution {
  goodIndices(s) {
    return solve(s);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, goodIndices, Solution };
}
