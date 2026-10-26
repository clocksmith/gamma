'use strict';

// 1961. Check If String Is a Prefix of Array (Easy).
// Specification: https://leetcode.com/problems/check-if-string-is-a-prefix-of-array/description/
// O(total compared characters) time, O(1) auxiliary space; accept only at whole-word boundaries.
function solve(s, words) {
  let matched = 0;
  for (const word of words) {
    if (!s.startsWith(word, matched)) return false;
    matched += word.length;
    if (matched === s.length) return true;
  }
  return false;
}

const isPrefixString = solve;
class Solution {
  isPrefixString(s, words) { return solve(s, words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isPrefixString };
