'use strict';

// 1992. Find All Groups of Farmland: identify each rectangular group by its top-left corner and trace its two dimensions.
// O(rows * columns) time and O(groups) output space with O(1) auxiliary space; inputs are read-only.
function solve(land) {
  const rows = land.length;
  const columns = land[0].length;
  const result = [];
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      if (land[row][column] === 0) continue;
      if (row > 0 && land[row - 1][column] === 1) continue;
      if (column > 0 && land[row][column - 1] === 1) continue;
      let bottom = row;
      let right = column;
      while (bottom + 1 < rows && land[bottom + 1][column] === 1) bottom += 1;
      while (right + 1 < columns && land[row][right + 1] === 1) right += 1;
      result.push([row, column, bottom, right]);
    }
  }
  return result;
}

const findFarmland = solve;
class Solution {
  findFarmland(land) { return solve(land); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findFarmland };
