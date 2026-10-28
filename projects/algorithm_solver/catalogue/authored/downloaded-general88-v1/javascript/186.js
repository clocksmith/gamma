'use strict';

// 186. Reverse Words in a String II (Medium).
// Specification: https://leetcode.com/problems/reverse-words-in-a-string-ii/description/
function solve(s) {
  const chars = s.slice();
  chars.reverse();
  let start = 0;
  for (let i = 0; i <= chars.length; i++) {
    if (i === chars.length || chars[i] === ' ') {
      let left = start; let right = i - 1;
      while (left < right) { const tmp = chars[left]; chars[left] = chars[right]; chars[right] = tmp; left++; right--; }
      start = i + 1;
    }
  }
  return chars;
}
const reverseWords = solve;
class Solution { reverseWords(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseWords };
