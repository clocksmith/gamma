'use strict';

// 1347. Minimum Number of Steps to Make Two Strings Anagram: sum positive letter deficits in the target string.
// O(n) time and O(1) auxiliary space for the fixed lowercase alphabet; inputs are read-only.
function solve(s, t) {
  const counts = new Int32Array(26);
  for (const letter of s) counts[letter.charCodeAt(0) - 97] += 1;
  for (const letter of t) counts[letter.charCodeAt(0) - 97] -= 1;
  let steps = 0;
  for (const count of counts) steps += Math.max(0, count);
  return steps;
}

const minSteps = solve;
class Solution {
  minSteps(s, t) { return solve(s, t); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSteps };
