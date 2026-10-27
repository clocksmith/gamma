'use strict';
// 304. Range Sum Query 2D - Immutable.
class NumMatrix {
  constructor(matrix) {
    const rows = matrix.length; const columns = rows ? matrix[0].length : 0;
    this.prefix = Array.from({ length: rows + 1 }, () => Array(columns + 1).fill(0));
    for (let row = 0; row < rows; row += 1) {
      let running = 0;
      for (let column = 0; column < columns; column += 1) {
        running += matrix[row][column];
        this.prefix[row + 1][column + 1] = this.prefix[row][column + 1] + running;
      }
    }
  }
  sumRegion(row1, col1, row2, col2) {
    const p = this.prefix;
    return p[row2 + 1][col2 + 1] - p[row1][col2 + 1] - p[row2 + 1][col1] + p[row1][col1];
  }
}
function solve(matrix, queries) {
  const structure = new NumMatrix(matrix);
  return queries.map(query => structure.sumRegion(...query));
}
if (typeof module !== 'undefined') module.exports = { solve, NumMatrix };
