'use strict';
// 308. Range Sum Query 2D - Mutable.
class NumMatrix {
  constructor(matrix) {
    this.rows = matrix.length; this.columns = this.rows ? matrix[0].length : 0;
    this.values = Array.from({ length: this.rows }, () => Array(this.columns).fill(0));
    this.tree = Array.from({ length: this.rows + 1 }, () => Array(this.columns + 1).fill(0));
    for (let row = 0; row < this.rows; row += 1) for (let column = 0; column < this.columns; column += 1) {
      this.update(row, column, matrix[row][column]);
    }
  }
  add(row, column, difference) {
    for (let r = row + 1; r <= this.rows; r += r & -r) {
      for (let c = column + 1; c <= this.columns; c += c & -c) this.tree[r][c] += difference;
    }
  }
  update(row, col, val) {
    const difference = val - this.values[row][col]; this.values[row][col] = val; this.add(row, col, difference);
  }
  prefix(row, column) {
    let total = 0;
    for (let r = row; r > 0; r -= r & -r) for (let c = column; c > 0; c -= c & -c) total += this.tree[r][c];
    return total;
  }
  sumRegion(row1, col1, row2, col2) {
    return this.prefix(row2 + 1, col2 + 1) - this.prefix(row1, col2 + 1)
      - this.prefix(row2 + 1, col1) + this.prefix(row1, col1);
  }
}
function solve(matrix, operations, args) {
  const structure = new NumMatrix(matrix);
  return operations.map((operation, index) => structure[operation](...args[index]));
}
if (typeof module !== 'undefined') module.exports = { solve, NumMatrix };
