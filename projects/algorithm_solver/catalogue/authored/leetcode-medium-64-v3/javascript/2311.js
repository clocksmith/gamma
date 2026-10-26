'use strict';

// 2311. Longest Binary Subsequence Less Than or Equal to K: keep every zero and greedily admit low-significance ones from the right.
// O(n) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(s, k) {
  let length = 0;
  let value = 0;
  let weight = 1;
  for (let index = s.length - 1; index >= 0; index -= 1) {
    if (s[index] === '0' || value + weight <= k) {
      if (s[index] === '1') value += weight;
      length += 1;
      weight = Math.min(k + 1, weight * 2);
    }
  }
  return length;
}

const longestSubsequence = solve;
class Solution {
  longestSubsequence(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestSubsequence };
