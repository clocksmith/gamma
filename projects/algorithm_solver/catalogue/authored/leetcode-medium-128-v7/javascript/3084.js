'use strict';

// 3084. Count Substrings Starting and Ending with Given Character: count ordered endpoint choices among occurrences of the required character.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s, c) {
  let occurrences = 0;
  for (const character of s) if (character === c) occurrences += 1;
  return occurrences * (occurrences + 1) / 2;
}

const countSubstrings = solve;
class Solution {
  countSubstrings(s, c) { return solve(s, c); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSubstrings };
