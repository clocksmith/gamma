'use strict';

// 2037. Minimum Number of Moves to Seat Everyone (Easy).
// Specification: https://leetcode.com/problems/minimum-number-of-moves-to-seat-everyone/description/
// O(n log n) time, O(n) space; pair both sorted copies in order.
function solve(seats, students) {
  const orderedSeats = seats.slice().sort((a, b) => a - b);
  const orderedStudents = students.slice().sort((a, b) => a - b);
  let moves = 0;
  for (let index = 0; index < seats.length; index++) moves += Math.abs(orderedSeats[index] - orderedStudents[index]);
  return moves;
}

const minMovesToSeat = solve;
class Solution {
  minMovesToSeat(seats, students) { return solve(seats, students); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMovesToSeat };
