'use strict';

// 131. Palindrome Partitioning (Medium).
// Specification: https://leetcode.com/problems/palindrome-partitioning/description/
function isPalindrome(text) { return text === [...text].reverse().join(''); }
function solve(s) {
  const result = [];
  function backtrack(start, current) {
    if (start === s.length) { result.push(current.slice()); return; }
    for (let end = start + 1; end <= s.length; end++) {
      const part = s.slice(start, end);
      if (isPalindrome(part)) { current.push(part); backtrack(end, current); current.pop(); }
    }
  }
  backtrack(0, []);
  return result;
}
const partition = solve;
class Solution { partition(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, partition };
