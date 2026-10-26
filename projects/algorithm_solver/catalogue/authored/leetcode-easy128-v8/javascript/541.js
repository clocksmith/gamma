'use strict';

// 541. Reverse String II (Easy).
// Specification: https://leetcode.com/problems/reverse-string-ii/description/
// O(n) time and space; reverse the first k characters in each 2k block.
function solve(s, k) {
  const result = s.split('');
  for (let start = 0; start < result.length; start += 2 * k) {
    let left = start;
    let right = Math.min(start + k, result.length) - 1;
    while (left < right) {
      [result[left], result[right]] = [result[right], result[left]];
      left++;
      right--;
    }
  }
  return result.join('');
}

const reverseStr = solve;
class Solution {
  reverseStr(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseStr };
