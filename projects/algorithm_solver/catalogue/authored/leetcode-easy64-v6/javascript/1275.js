'use strict';

// 1275. Find Winner on a Tic Tac Toe Game (Easy).
// Specification: https://leetcode.com/problems/find-winner-on-a-tic-tac-toe-game/description/
// O(len(moves)) time, O(1) space on the 3-by-3 board; preserve moves.
function solve(moves) {
  const rows = [0, 0, 0];
  const columns = [0, 0, 0];
  let mainDiagonal = 0;
  let otherDiagonal = 0;
  for (let turn = 0; turn < moves.length; turn++) {
    const [row, column] = moves[turn];
    const mark = turn % 2 === 0 ? 1 : -1;
    rows[row] += mark;
    columns[column] += mark;
    if (row === column) mainDiagonal += mark;
    if (row + column === 2) otherDiagonal += mark;
    if (Math.abs(rows[row]) === 3 || Math.abs(columns[column]) === 3 ||
        Math.abs(mainDiagonal) === 3 || Math.abs(otherDiagonal) === 3) {
      return mark === 1 ? 'A' : 'B';
    }
  }
  return moves.length === 9 ? 'Draw' : 'Pending';
}

const tictactoe = solve;
class Solution {
  tictactoe(moves) { return solve(moves); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, tictactoe };
