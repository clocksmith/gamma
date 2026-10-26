'use strict';

// 1208. Get Equal Substrings Within Budget: maintain the longest affordable sliding window.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s, t, maxCost) {
  let left = 0;
  let total = 0;
  let best = 0;
  for (let right = 0; right < s.length; right += 1) {
    total += Math.abs(s.charCodeAt(right) - t.charCodeAt(right));
    while (total > maxCost) {
      total -= Math.abs(s.charCodeAt(left) - t.charCodeAt(left));
      left += 1;
    }
    best = Math.max(best, right - left + 1);
  }
  return best;
}

const equalSubstring = solve;
class Solution {
  equalSubstring(s, t, maxCost) { return solve(s, t, maxCost); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, equalSubstring };
