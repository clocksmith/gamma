// Original implementation. Contract: https://leetcode.com/problems/count-submatrices-with-equal-frequency-of-x-and-y/
"use strict";

function solve(grid) {
  const columns = grid[0].length;
  const balance = Array(columns).fill(0);
  const xCount = Array(columns).fill(0);
  let answer = 0;
  // A submatrix containing (0,0) is uniquely specified by its bottom-right cell.
  for (const row of grid) {
    let rowBalance = 0;
    let rowXCount = 0;
    for (let column = 0; column < columns; column++) {
      rowBalance += (row[column] === "X") - (row[column] === "Y");
      rowXCount += row[column] === "X";
      balance[column] += rowBalance;
      xCount[column] += rowXCount;
      if (balance[column] === 0 && xCount[column] > 0) answer++;
    }
  }
  return answer;
}

module.exports = solve;
