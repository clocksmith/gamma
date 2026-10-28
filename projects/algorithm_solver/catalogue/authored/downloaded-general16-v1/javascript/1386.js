'use strict';

// 1386. Cinema Seat Allocation (Medium).
// Specification: https://leetcode.com/problems/cinema-seat-allocation/description/
function solve(n, reservedSeats) {
  const rows = new Map();
  for (const [row, seat] of reservedSeats) {
    if (!rows.has(row)) rows.set(row, new Set());
    rows.get(row).add(seat);
  }
  let families = (n - rows.size) * 2;
  for (const seats of rows.values()) {
    const left = ![2, 3, 4, 5].some((seat) => seats.has(seat));
    const middle = ![4, 5, 6, 7].some((seat) => seats.has(seat));
    const right = ![6, 7, 8, 9].some((seat) => seats.has(seat));
    if (left && right) families += 2; else if (left || middle || right) families += 1;
  }
  return families;
}
const maxNumberOfFamilies = solve;
class Solution { maxNumberOfFamilies(...args) { return solve(...args); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxNumberOfFamilies };
