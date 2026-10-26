'use strict';

// 3168. Minimum Number of Chairs in a Waiting Room (Easy).
// Specification: https://leetcode.com/problems/minimum-number-of-chairs-in-a-waiting-room/description/
// O(n) time, O(1) auxiliary space; the entry/exit sequence is valid.
function solve(s) {
  let occupied = 0;
  let maximum = 0;
  for (const event of s) {
    occupied += event === 'E' ? 1 : -1;
    maximum = Math.max(maximum, occupied);
  }
  return maximum;
}

const minimumChairs = solve;
class Solution {
  minimumChairs(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumChairs };
