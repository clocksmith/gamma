'use strict';

// 3090. Maximum Length Substring With Two Occurrences (Easy).
// Specification: https://leetcode.com/problems/maximum-length-substring-with-two-occurrences/description/
// O(n) time, O(1) alphabet space; maintain at most two copies of each letter.
function solve(s) {
  const counts = new Array(26).fill(0);
  let left = 0;
  let longest = 0;
  for (let right = 0; right < s.length; right++) {
    const added = s.charCodeAt(right) - 97;
    counts[added]++;
    while (counts[added] > 2) {
      counts[s.charCodeAt(left) - 97]--;
      left++;
    }
    longest = Math.max(longest, right - left + 1);
  }
  return longest;
}

const maximumLengthSubstring = solve;
class Solution {
  maximumLengthSubstring(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumLengthSubstring };
