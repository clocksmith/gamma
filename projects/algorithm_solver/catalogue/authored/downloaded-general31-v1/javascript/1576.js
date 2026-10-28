'use strict';

// 1576. Replace All ?'s to Avoid Consecutive Repeating Characters (Medium).
// Specification: https://leetcode.com/problems/replace-all-s-to-avoid-consecutive-repeating-characters/description/
function solve(s) {
  const chars = [...s];
  for (let i = 0; i < chars.length; i++) {
    if (chars[i] !== '?') continue;
    for (const candidate of ['a', 'b', 'c']) {
      const left = i > 0 ? chars[i - 1] : '';
      const right = i + 1 < chars.length ? chars[i + 1] : '';
      if (candidate !== left && candidate !== right) { chars[i] = candidate; break; }
    }
  }
  return chars.join('');
}
const modifyString = solve;
class Solution { modifyString(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, modifyString };
