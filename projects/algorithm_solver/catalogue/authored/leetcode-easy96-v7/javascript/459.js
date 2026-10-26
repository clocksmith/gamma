'use strict';

// 459. Repeated Substring Pattern (Easy).
// Specification: https://leetcode.com/problems/repeated-substring-pattern/description/
// O(n) time and space; the longest proper border determines a candidate period.
function solve(s) {
  const prefix = new Array(s.length).fill(0);
  for (let index = 1; index < s.length; index++) {
    let matched = prefix[index - 1];
    while (matched > 0 && s[index] !== s[matched]) matched = prefix[matched - 1];
    if (s[index] === s[matched]) matched++;
    prefix[index] = matched;
  }
  const border = prefix[s.length - 1];
  return border > 0 && s.length % (s.length - border) === 0;
}

const repeatedSubstringPattern = solve;
class Solution {
  repeatedSubstringPattern(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, repeatedSubstringPattern };
