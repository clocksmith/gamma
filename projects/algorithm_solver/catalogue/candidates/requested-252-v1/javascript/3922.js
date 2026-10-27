/**
 * 3922. Minimum Flips to Make Binary String Coherent
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-flips-to-make-binary-string-coherent/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3922.Minimum%20Flips%20to%20Make%20Binary%20String%20Coherent/README_EN.md
 * Complexity: O(n) time, O(1) space.
 * Coherent shapes: all ones; at most one one; or exactly two ones at the ends and zeros inside. Forbidden patterns are subsequences. Native name pending.
 */

function solve(s) {
  let ones = 0;
  for (const character of s) if (character === '1') ones += 1;
  let answer = Math.min(s.length - ones, Math.max(0, ones - 1));
  if (s.length >= 2) {
    const first = s[0] === '1' ? 1 : 0;
    const last = s[s.length - 1] === '1' ? 1 : 0;
    answer = Math.min(answer, ones - first - last + 2 - first - last);
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
