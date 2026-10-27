/**
 * 3980. Minimum Operations to Transform Binary String
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-operations-to-transform-binary-string/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3980.Minimum%20Operations%20to%20Transform%20Binary%20String/README_EN.md
 * Complexity: O(n) time, O(1) auxiliary space.
 * A reset edge covers required 1->0 vertices. Each reset costs three operations after accounting for net bit-count change; minimum edges pair adjacent required vertices. Singletons can use either neighbor when n>1. Native method unconfirmed; solve is the explicit entry point.
 */

function solve(s1, s2) {
  if (s1.length === 1) return s1 === '1' && s2 === '0' ? -1 : Number(s1 !== s2);
  let baseline = 0, resets = 0, run = 0;
  for (let i = 0; i < s1.length; i++) {
    baseline += Number(s2[i]) - Number(s1[i]);
    if (s1[i] === '1' && s2[i] === '0') run++;
    else { resets += Math.floor((run + 1) / 2); run = 0; }
  }
  return baseline + 3 * (resets + Math.floor((run + 1) / 2));
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
