'use strict';

// 567. Permutation in String (Medium).
// Specification: https://leetcode.com/problems/permutation-in-string/description/
function solve(s1, s2) {
  if (s1.length > s2.length) return false;
  const need = new Array(26).fill(0);
  const window = new Array(26).fill(0);
  for (const ch of s1) need[ch.charCodeAt(0) - 97]++;
  for (let i = 0; i < s2.length; i++) {
    window[s2[i].charCodeAt(0) - 97]++;
    if (i >= s1.length) window[s2[i - s1.length].charCodeAt(0) - 97]--;
    if (window.join(',') === need.join(',')) return true;
  }
  return false;
}
const checkInclusion = solve;
class Solution { checkInclusion(s1, s2) { return solve(s1, s2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkInclusion };
