'use strict';

// 2186. Minimum Number of Steps to Make Two Strings Anagram II: sum the unmatched counts in both strings.
// O(len(s) + len(t)) time and O(1) auxiliary space for lowercase English letters; inputs are read-only.
function solve(s, t) {
  const differences = new Array(26).fill(0);
  for (let index = 0; index < s.length; index += 1) {
    differences[s.charCodeAt(index) - 97] += 1;
  }
  for (let index = 0; index < t.length; index += 1) {
    differences[t.charCodeAt(index) - 97] -= 1;
  }
  let answer = 0;
  for (const difference of differences) answer += Math.abs(difference);
  return answer;
}

const minSteps = solve;
class Solution {
  minSteps(s, t) { return solve(s, t); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSteps };
