'use strict';

// 603. Consecutive Available Seats. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. cinema: seat_id, free (0/1 or boolean). Output: seat_id in ascending order.

function solve(cinema) {
  const free = new Set(cinema.filter(row => row.free === 1 || row.free === true).map(row => row.seat_id));
  return [...free].sort((a, b) => a - b).filter(seat => free.has(seat - 1) || free.has(seat + 1)).map(seat => ({seat_id: seat}));
}

const consecutiveSeats = solve;
class Solution {
  consecutiveSeats(cinema) { return solve(cinema); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, consecutiveSeats };
