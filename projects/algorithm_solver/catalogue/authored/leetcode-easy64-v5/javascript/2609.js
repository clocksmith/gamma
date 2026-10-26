'use strict';

// 2609. Find the Longest Balanced Substring of a Binary String (Easy).
// Specification: https://leetcode.com/problems/find-the-longest-balanced-substring-of-a-binary-string/description/
// O(n) time, O(1) auxiliary space; preserve s.
function solve(s) {
  let zeros = 0;
  let ones = 0;
  let longest = 0;
  for (const character of s) {
    if (character === '0') {
      if (ones > 0) {
        zeros = 0;
        ones = 0;
      }
      zeros++;
    } else {
      ones++;
      longest = Math.max(longest, 2 * Math.min(zeros, ones));
    }
  }
  return longest;
}

const findTheLongestBalancedSubstring = solve;
class Solution {
  findTheLongestBalancedSubstring(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findTheLongestBalancedSubstring };
