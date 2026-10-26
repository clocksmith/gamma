'use strict';

// 2423. Remove Letter To Equalize Frequency (Easy).
// Specification: https://leetcode.com/problems/remove-letter-to-equalize-frequency/description/
// O(n + 26^2) time, O(26) space; try removing one occurrence of each present letter.
function solve(word) {
  const counts = new Array(26).fill(0);
  for (const character of word) counts[character.charCodeAt(0) - 97]++;
  for (let removed = 0; removed < counts.length; removed++) {
    if (counts[removed] === 0) continue;
    counts[removed]--;
    let expected = 0;
    let valid = true;
    for (const count of counts) {
      if (count === 0) continue;
      if (expected === 0) expected = count;
      else if (count !== expected) {
        valid = false;
        break;
      }
    }
    counts[removed]++;
    if (valid) return true;
  }
  return false;
}

const equalFrequency = solve;
class Solution {
  equalFrequency(word) { return solve(word); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, equalFrequency };
