'use strict';

// 1227. Airplane Seat Assignment Probability (Medium).
// Specification: https://leetcode.com/problems/airplane-seat-assignment-probability/description/
function solve(n) {
  return n === 1 ? 1.0 : 0.5;
}
const nthPersonGetsNthSeat = solve;
class Solution { nthPersonGetsNthSeat(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, nthPersonGetsNthSeat };
