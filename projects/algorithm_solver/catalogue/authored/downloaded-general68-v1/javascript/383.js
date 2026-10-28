'use strict';

// 383. Ransom Note (Easy).
// Specification: https://leetcode.com/problems/ransom-note/description/
function solve(ransomNote, magazine) {
  const counts = {};
  for (const ch of magazine) counts[ch] = (counts[ch] || 0) + 1;
  for (const ch of ransomNote) {
    if ((counts[ch] || 0) === 0) return false;
    counts[ch]--;
  }
  return true;
}
const canConstruct = solve;
class Solution { canConstruct(ransomNote, magazine) { return solve(ransomNote, magazine); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canConstruct };
