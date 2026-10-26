'use strict';

// 3256. Maximum Value Sum by Placing Three Rooks I.
// Enumerate the middle rook and the three best distinct columns above and below it; O(rows*columns) time and O(rows+columns) space. Inputs are preserved.

function solve(board) {
  const rows = board.length, columns = board[0].length;
  function topThree(values) {
    const best = [];
    for (let column = 0; column < columns; column += 1) {
      best.push([values[column], column]);
      best.sort((a, b) => b[0] - a[0] || b[1] - a[1]);
      if (best.length > 3) best.pop();
    }
    return best;
  }
  const below = Array(rows);
  let values = Array(columns).fill(-Infinity);
  for (let row = rows - 1; row >= 0; row -= 1) {
    below[row] = topThree(values);
    for (let column = 0; column < columns; column += 1) values[column] = Math.max(values[column], board[row][column]);
  }
  values = board[0].slice();
  let answer = -Infinity;
  for (let row = 1; row + 1 < rows; row += 1) {
    const above = topThree(values);
    for (let column = 0; column < columns; column += 1) {
      for (const [first, firstColumn] of above) {
        if (firstColumn === column) continue;
        for (const [last, lastColumn] of below[row]) {
          if (lastColumn !== column && lastColumn !== firstColumn) answer = Math.max(answer, first + board[row][column] + last);
        }
      }
    }
    for (let column = 0; column < columns; column += 1) values[column] = Math.max(values[column], board[row][column]);
  }
  return answer;
}

const maximumValueSum = solve;
class Solution {
  maximumValueSum(board) { return solve(board); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumValueSum };
