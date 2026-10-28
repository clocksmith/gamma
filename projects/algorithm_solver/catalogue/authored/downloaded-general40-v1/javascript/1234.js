'use strict';

// 1234. Replace the Substring for Balanced String (Medium).
// Specification: https://leetcode.com/problems/replace-the-substring-for-balanced-string/description/
function solve(s) {
  const n = s.length; const target = n / 4;
  const counts = { Q: 0, W: 0, E: 0, R: 0 };
  for (const ch of s) counts[ch]++;
  if (counts['Q'] === target && counts['W'] === target && counts['E'] === target && counts['R'] === target) return 0;
  let best = n; let left = 0;
  const window = { Q: 0, W: 0, E: 0, R: 0 };
  function outsideOk() { return counts['Q'] - window['Q'] <= target && counts['W'] - window['W'] <= target && counts['E'] - window['E'] <= target && counts['R'] - window['R'] <= target; }
  for (let right = 0; right < n; right++) {
    window[s[right]]++;
    while (left <= right && outsideOk()) { best = Math.min(best, right - left + 1); window[s[left]]--; left++; }
  }
  return best;
}
const balancedString = solve;
class Solution { balancedString(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, balancedString };
