'use strict';

// 2414. Length of the Longest Alphabetical Continuous Substring: extend a run only when the next letter advances by one.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s) {
  let current = 0;
  let answer = 0;
  for (let index = 0; index < s.length; index += 1) {
    if (index > 0 && s.charCodeAt(index) === s.charCodeAt(index - 1) + 1) current += 1;
    else current = 1;
    answer = Math.max(answer, current);
  }
  return answer;
}

const longestContinuousSubstring = solve;
class Solution {
  longestContinuousSubstring(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestContinuousSubstring };
