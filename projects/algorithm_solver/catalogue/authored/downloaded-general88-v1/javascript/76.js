'use strict';

// 76. Minimum Window Substring (Hard).
// Specification: https://leetcode.com/problems/minimum-window-substring/description/
function solve(s, t) {
  if (t.length === 0) return '';
  const need = {};
  for (const ch of t) need[ch] = (need[ch] || 0) + 1;
  const required = Object.keys(need).length;
  let formed = 0; const window = {}; let left = 0; let best = [Infinity, 0, 0];
  for (let right = 0; right < s.length; right++) {
    const ch = s[right];
    window[ch] = (window[ch] || 0) + 1;
    if (need[ch] !== undefined && window[ch] === need[ch]) formed++;
    while (formed === required) {
      if (right - left + 1 < best[0]) best = [right - left + 1, left, right];
      const leftCh = s[left];
      window[leftCh]--;
      if (need[leftCh] !== undefined && window[leftCh] < need[leftCh]) formed--;
      left++;
    }
  }
  return best[0] === Infinity ? '' : s.slice(best[1], best[2] + 1);
}
const minWindow = solve;
class Solution { minWindow(s, t) { return solve(s, t); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minWindow };
