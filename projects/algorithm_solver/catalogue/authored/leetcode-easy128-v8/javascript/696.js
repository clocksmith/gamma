'use strict';

// 696. Count Binary Substrings (Easy).
// Specification: https://leetcode.com/problems/count-binary-substrings/description/
// O(n) time, O(1) space; each adjacent pair of runs contributes its smaller length.
function solve(s) {
  let previous = 0;
  let current = 1;
  let total = 0;
  for (let index = 1; index < s.length; index++) {
    if (s[index] === s[index - 1]) current++;
    else {
      total += Math.min(previous, current);
      previous = current;
      current = 1;
    }
  }
  return total + Math.min(previous, current);
}

const countBinarySubstrings = solve;
class Solution {
  countBinarySubstrings(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countBinarySubstrings };
