'use strict';

// 1684. Count the Number of Consistent Strings (Easy).
// Specification: https://leetcode.com/problems/count-the-number-of-consistent-strings/description/
function solve(allowed, words) {
  const allowedSet = new Set(allowed);
  let count = 0;
  for (const word of words) { if ([...word].every((ch) => allowedSet.has(ch))) count++; }
  return count;
}
const countConsistentStrings = solve;
class Solution { countConsistentStrings(allowed, words) { return solve(allowed, words); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, countConsistentStrings };
