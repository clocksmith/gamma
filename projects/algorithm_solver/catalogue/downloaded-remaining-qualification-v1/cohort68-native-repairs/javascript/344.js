'use strict';

// 344. Reverse String (Easy).
// Specification: https://leetcode.com/problems/reverse-string/description/
function solve(s) {
  return s.slice().reverse();
}
const reverseString = solve;
class Solution { reverseString(s) {
  let left = 0, right = s.length - 1;
  while (left < right) {
    const ch = s[left]; s[left] = s[right]; s[right] = ch; left++; right--;
  }
} }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseString };
