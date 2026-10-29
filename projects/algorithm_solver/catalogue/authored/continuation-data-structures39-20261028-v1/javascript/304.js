"use strict";

class NumMatrix {
  constructor(matrix) {
    const m = matrix.length;
    const n = m > 0 ? matrix[0].length : 0;
    const pref = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
    for (let r = 0; r < m; r++) {
      let rowSum = 0;
      const row = matrix[r];
      const prev = pref[r];
      const curr = pref[r + 1];
      for (let c = 0; c < n; c++) {
        rowSum += row[c];
        curr[c + 1] = prev[c + 1] + rowSum;
      }
    }
    this.pref = pref;
  }
  sumRegion(row1, col1, row2, col2) {
    const p = this.pref;
    return p[row2 + 1][col2 + 1] - p[row1][col2 + 1] - p[row2 + 1][col1] + p[row1][col1];
  }
}

function solve(operation_names, argument_lists) {
  const instance = new NumMatrix(argument_lists[0][0]);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i];
    const args = argument_lists[i];
    if (op === "sumRegion") {
      out.push(instance.sumRegion(args[0], args[1], args[2], args[3]));
    } else {
      throw new Error("unknown operation");
    }
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.NumMatrix = NumMatrix;
