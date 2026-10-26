'use strict';

// 3442. Maximum Difference Between Even and Odd Frequency I (Easy).
// Specification: https://leetcode.com/problems/maximum-difference-between-even-and-odd-frequency-i/description/
// O(n) time, O(1) alphabet space; zero frequencies are not eligible even frequencies.
function solve(s) {
  const counts = new Array(26).fill(0);
  for (const character of s) counts[character.charCodeAt(0) - 97]++;
  let largestOdd = 0;
  let smallestEven = Infinity;
  for (const count of counts) {
    if (count % 2 === 1) largestOdd = Math.max(largestOdd, count);
    else if (count > 0) smallestEven = Math.min(smallestEven, count);
  }
  return largestOdd - smallestEven;
}

const maxDifference = solve;
class Solution {
  maxDifference(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxDifference };
