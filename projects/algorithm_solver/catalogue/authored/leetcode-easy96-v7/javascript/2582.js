'use strict';

// 2582. Pass the Pillow (Easy).
// Specification: https://leetcode.com/problems/pass-the-pillow/description/
// O(1) time and space; fold the elapsed time into a back-and-forth period of 2(n - 1).
function solve(n, time) {
  const period = 2 * (n - 1);
  const position = time % period;
  return position < n ? position + 1 : period - position + 1;
}

const passThePillow = solve;
class Solution {
  passThePillow(n, time) { return solve(n, time); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, passThePillow };
