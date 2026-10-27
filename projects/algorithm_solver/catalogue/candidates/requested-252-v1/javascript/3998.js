/**
 * 3998. Transform Binary String Using Subsequence Sort
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/transform-binary-string-using-subsequence-sort/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3998.Transform%20Binary%20String%20Using%20Subsequence%20Sort/README_EN.md
 * Complexity: O(|s| + sum |strs[i]|) time, O(|s|) auxiliary space.
 * Reachability preserves total zeros and can only move zeros left. Earliest possible wildcard zeros maximize every prefix, so they provide a complete feasibility check. Native method unconfirmed.
 */

function solve(s, strs) {
  const prefix = new Int32Array(s.length + 1);
  for (let i = 0; i < s.length; i++) prefix[i + 1] = prefix[i] + Number(s[i] === '0');
  const total = prefix[s.length];
  return strs.map(pattern => {
    let forced = 0, wild = 0;
    for (const ch of pattern) { forced += Number(ch === '0'); wild += Number(ch === '?'); }
    let extra = total - forced;
    if (extra < 0 || extra > wild) return false;
    let zeros = 0;
    for (let i = 0; i < pattern.length; i++) {
      if (pattern[i] === '0') zeros++;
      else if (pattern[i] === '?' && extra > 0) { zeros++; extra--; }
      if (zeros < prefix[i + 1]) return false;
    }
    return true;
  });
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
