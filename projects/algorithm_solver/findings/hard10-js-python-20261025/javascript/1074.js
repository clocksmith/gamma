/**
 * 1074. Number of Submatrices That Sum to Target (Hard).
 * Fresh candidate authored in this conversation; no repository solution copied.
 * Specification: https://leetcode.com/problems/number-of-submatrices-that-sum-to-target/description/
 * Canonical API: solve(matrix, target); native alias: numSubmatrixSumTarget(matrix, target).
 * Inputs are preserved. Gamma independent qualification is pending.
 */
'use strict';

function solve(matrix, target) {
  if (matrix.length === 0 || matrix[0].length === 0) {
    return 0;
  }
  const rows = matrix.length;
  const columns = matrix[0].length;
  const pairRows = rows <= columns;
  const boundaryCount = Math.min(rows, columns);
  const lineLength = Math.max(rows, columns);
  let total = 0;

  for (let start = 0; start < boundaryCount; start++) {
    const line = new Array(lineLength).fill(0);
    for (let end = start; end < boundaryCount; end++) {
      for (let position = 0; position < lineLength; position++) {
        line[position] += pairRows ? matrix[end][position] : matrix[position][end];
      }
      const frequencies = new Map([[0, 1]]);
      let prefix = 0;
      for (const value of line) {
        prefix += value;
        total += frequencies.get(prefix - target) || 0;
        frequencies.set(prefix, (frequencies.get(prefix) || 0) + 1);
      }
    }
  }
  return total;
}

function numSubmatrixSumTarget(matrix, target) {
  return solve(matrix, target);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, numSubmatrixSumTarget };
}
