'use strict';

// 626. Exchange Seats. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. seat: id, student; IDs are consecutive from 1. Output: id, student; final unpaired seat remains unchanged.

function solve(seat) {
  const rows = seat.slice().sort((a, b) => a.id - b.id);
  return rows.map((row, i) => {
    const partner = i % 2 === 0 && i + 1 < rows.length ? i + 1 : i % 2 === 1 ? i - 1 : i;
    return {id: row.id, student: rows[partner].student};
  });
}

const exchangeSeats = solve;
class Solution {
  exchangeSeats(seat) { return solve(seat); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, exchangeSeats };
