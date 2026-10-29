"use strict";

function solve(mat1, mat2) {
  const m = mat1.length, k = mat1[0].length, n = mat2[0].length;
  const res = Array.from({ length: m }, () => new Array(n).fill(0));
  for (let i = 0; i < m; i++) {
    for (let p = 0; p < k; p++) {
      const v1 = mat1[i][p];
      if (v1 !== 0) {
        for (let j = 0; j < n; j++) {
          if (mat2[p][j] !== 0) res[i][j] += v1 * mat2[p][j];
        }
      }
    }
  }
  return res;
}

function multiply(mat1, mat2) {
  return solve(mat1, mat2);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.multiply = multiply;
