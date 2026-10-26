'use strict';

// 859. Buddy Strings (Easy).
// Specification: https://leetcode.com/problems/buddy-strings/description/
// O(n) time, O(1) space for lowercase English; exactly one swap must be possible.
function solve(s, goal) {
  if (s.length !== goal.length) return false;
  const mismatches = [];
  const seen = new Set();
  let hasDuplicate = false;
  for (let index = 0; index < s.length; index++) {
    if (seen.has(s[index])) hasDuplicate = true;
    seen.add(s[index]);
    if (s[index] !== goal[index]) {
      mismatches.push(index);
      if (mismatches.length > 2) return false;
    }
  }
  if (mismatches.length === 0) return hasDuplicate;
  if (mismatches.length !== 2) return false;
  const [first, second] = mismatches;
  return s[first] === goal[second] && s[second] === goal[first];
}

const buddyStrings = solve;
class Solution {
  buddyStrings(s, goal) { return solve(s, goal); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, buddyStrings };
