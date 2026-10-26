'use strict';

// 242. Valid Anagram (Easy).
// Specification: https://leetcode.com/problems/valid-anagram/description/
// O(n + m) time, O(1) space for the declared lowercase-English alphabet.
function solve(s, t) {
  if (s.length !== t.length) return false;
  const counts = new Array(26).fill(0);
  for (let index = 0; index < s.length; index++) {
    counts[s.charCodeAt(index) - 97]++;
    counts[t.charCodeAt(index) - 97]--;
  }
  return counts.every(count => count === 0);
}

const isAnagram = solve;
class Solution {
  isAnagram(s, t) { return solve(s, t); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isAnagram };
