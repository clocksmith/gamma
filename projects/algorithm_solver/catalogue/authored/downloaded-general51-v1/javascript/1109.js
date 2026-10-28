'use strict';

// 1109. Corporate Flight Bookings (Medium).
// Specification: https://leetcode.com/problems/corporate-flight-bookings/description/
function solve(bookings, n) {
  const diff = new Array(n + 1).fill(0);
  for (const [first, last, seats] of bookings) { diff[first - 1] += seats; if (last < n) diff[last] -= seats; }
  const result = [];
  let current = 0;
  for (let i = 0; i < n; i++) { current += diff[i]; result.push(current); }
  return result;
}
const corpFlightBookings = solve;
class Solution { corpFlightBookings(bookings, n) { return solve(bookings, n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, corpFlightBookings };
