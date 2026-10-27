/**
 * 3662. Filter Characters by Frequency
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(s, k).
 * Algorithm: Count globally, then filter in original order.
 * Complexity: O(n) time; O(n) output space and O(26) counting space.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/filter-characters-by-frequency/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3662.Filter%20Characters%20by%20Frequency/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 */

function solve(s, k) {
  const counts = new Int32Array(26);
  for (let index = 0; index < s.length; index += 1) counts[s.charCodeAt(index) - 97] += 1;
  const kept = [];
  for (let index = 0; index < s.length; index += 1) {
    if (counts[s.charCodeAt(index) - 97] < k) kept.push(s[index]);
  }
  return kept.join("");
}

function filterCharacters(s, k) {
  return solve(s, k);
}

class Solution {
  filterCharacters(s, k) {
    return solve(s, k);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, filterCharacters, Solution };
}
