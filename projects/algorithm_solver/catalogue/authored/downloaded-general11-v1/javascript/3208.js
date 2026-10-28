'use strict';

// 3208. Alternating Groups II (Medium).
// Specification: https://leetcode.com/problems/alternating-groups-ii/description/
function solve(colors, k) {
  const n = colors.length; let ans = 0;
  for (let i = 0; i < n; i++) {
    let ok = true;
    for (let j = 0; j + 1 < k; j++) {
      if (colors[(i + j) % n] === colors[(i + j + 1) % n]) { ok = false; break; }
    }
    if (ok) ans++;
  }
  return ans;
}
const numberOfAlternatingGroups = solve;
class Solution { numberOfAlternatingGroups(colors, k) { return solve(colors, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfAlternatingGroups };
