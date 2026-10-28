'use strict';

// 438. Find All Anagrams in a String (Medium).
// Specification: https://leetcode.com/problems/find-all-anagrams-in-a-string/description/
function solve(s, p) {
  const result = [];
  if (p.length > s.length) return result;
  const need = new Array(26).fill(0);
  const window = new Array(26).fill(0);
  for (const ch of p) need[ch.charCodeAt(0) - 97]++;
  for (let i = 0; i < s.length; i++) {
    window[s[i].charCodeAt(0) - 97]++;
    if (i >= p.length) window[s[i - p.length].charCodeAt(0) - 97]--;
    let matches = true;
    for (let d = 0; d < 26; d++) { if (window[d] !== need[d]) { matches = false; break; } }
    if (i >= p.length - 1 && matches) result.push(i - p.length + 1);
  }
  return result;
}
const findAnagrams = solve;
class Solution { findAnagrams(s, p) { return solve(s, p); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findAnagrams };
