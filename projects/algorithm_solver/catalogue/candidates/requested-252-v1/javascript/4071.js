/**
 * 4071. Minimum Rotations to Dial a Number II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-rotations-to-dial-a-number-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4071.Minimum%20Rotations%20to%20Dial%20a%20Number%20II/README_EN.md
 * Complexity: O(n) time, O(1) space.
 * Reversing a suffix preserves every internal edge cost because dial distance is symmetric. Only the entering edge changes; k=0 uses the initial pointer zero. Reversal itself has no rotation charge. n equals s.length.
 */

function solve(n,s) {
  function distance(a,b){const d=Math.abs(a-b);return Math.min(d,10-d);}
  let previous=0,total=0,adjustment=0;const last=Number(s[s.length-1]);
  for(const character of s){const digit=Number(character),original=distance(previous,digit);total+=original;adjustment=Math.min(adjustment,distance(previous,last)-original);previous=digit;}
  return total+adjustment;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
