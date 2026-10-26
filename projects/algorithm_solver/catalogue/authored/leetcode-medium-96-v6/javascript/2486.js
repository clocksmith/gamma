'use strict';

// 2486. Append Characters to String to Make Subsequence: greedily match the longest target prefix before appending its remaining suffix.
// O(len(s)) time and O(1) auxiliary space; inputs are read-only.
function solve(s, t) {
  let matched = 0;
  for (const character of s) {
    if (matched < t.length && character === t[matched]) matched += 1;
  }
  return t.length - matched;
}

const appendCharacters = solve;
class Solution {
  appendCharacters(s, t) { return solve(s, t); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, appendCharacters };
