'use strict';

// 28. Find the Index of the First Occurrence in a String (Easy).
// Specification: https://leetcode.com/problems/find-the-index-of-the-first-occurrence-in-a-string/description/
// O(n + m) time, O(m) space; KMP prefix links avoid repeated comparisons.
function solve(haystack, needle) {
  if (needle.length === 0) return 0;
  const prefix = new Array(needle.length).fill(0);
  for (let index = 1, matched = 0; index < needle.length; index++) {
    while (matched > 0 && needle[index] !== needle[matched]) matched = prefix[matched - 1];
    if (needle[index] === needle[matched]) matched++;
    prefix[index] = matched;
  }
  let matched = 0;
  for (let index = 0; index < haystack.length; index++) {
    while (matched > 0 && haystack[index] !== needle[matched]) matched = prefix[matched - 1];
    if (haystack[index] === needle[matched]) matched++;
    if (matched === needle.length) return index - needle.length + 1;
  }
  return -1;
}

const strStr = solve;
class Solution {
  strStr(haystack, needle) { return solve(haystack, needle); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, strStr };
