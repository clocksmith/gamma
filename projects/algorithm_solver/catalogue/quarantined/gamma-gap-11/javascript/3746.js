'use strict';

// 3746. Minimum String Length After Balanced Removals.
// O(n) time and O(1) auxiliary space; balanced removals preserve the difference in letter counts.
function solve(s) {
  let balance = 0;
  for (const char of s) balance += char === 'a' ? 1 : -1;
  return Math.abs(balance);
}

const minLengthAfterRemovals = solve;
class Solution {
  minLengthAfterRemovals(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minLengthAfterRemovals };
