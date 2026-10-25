'use strict';

// 1540. Can Convert String in K Moves: assign each repeated shift its next available move.
// O(n) time and O(1) auxiliary space for lowercase English letters; inputs are read-only.
function solve(s, t, k) {
  if (s.length !== t.length) return false;
  const counts = new Array(26).fill(0);
  for (let index = 0; index < s.length; index += 1) {
    const shift = (t.charCodeAt(index) - s.charCodeAt(index) + 26) % 26;
    if (shift === 0) continue;
    const move = shift + 26 * counts[shift];
    if (move > k) return false;
    counts[shift] += 1;
  }
  return true;
}

const canConvertString = solve;
class Solution {
  canConvertString(s, t, k) { return solve(s, t, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canConvertString };
