'use strict';

// 796. Rotate String (Easy).
// Specification: https://leetcode.com/problems/rotate-string/description/
// O(n^2) worst-case time, O(n) space; equal-length rotations occur in the doubled string.
function solve(s, goal) {
  return s.length === goal.length && (s + s).includes(goal);
}

const rotateString = solve;
class Solution {
  rotateString(s, goal) { return solve(s, goal); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, rotateString };
