/**
 * 3773. Maximum Number of Equal Length Runs
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(s).
 * Algorithm: Count maximal runs by length and return the largest frequency.
 * Complexity: O(n) time; O(n) space.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/maximum-number-of-equal-length-runs/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3773.Maximum%20Number%20of%20Equal%20Length%20Runs/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 */

function solve(s) {
  const lengthCounts = new Map();
  let answer = 0;
  for (let start = 0; start < s.length;) {
    let end = start + 1;
    while (end < s.length && s[end] === s[start]) end += 1;
    const length = end - start;
    const count = (lengthCounts.get(length) || 0) + 1;
    lengthCounts.set(length, count);
    answer = Math.max(answer, count);
    start = end;
  }
  return answer;
}

function maxSameLengthRuns(s) {
  return solve(s);
}

class Solution {
  maxSameLengthRuns(s) {
    return solve(s);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, maxSameLengthRuns, Solution };
}
