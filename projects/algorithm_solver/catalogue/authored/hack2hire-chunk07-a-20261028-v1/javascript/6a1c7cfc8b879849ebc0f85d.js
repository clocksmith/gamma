"use strict";
// Hack2Hire 6a1c7cfc8b879849ebc0f85d (Max Matrix Border Distinct Sum) over an INFERRED spec; qualification unknown.

function solve(matrix, frameSize) {
  const k = frameSize, m = matrix.length, n = matrix[0].length;
  let best = null;
  const seen = new Set();
  for (let r = 0; r + k <= m; r++) {
    const top = matrix[r], bottom = matrix[r + k - 1];
    for (let c = 0; c + k <= n; c++) {
      seen.clear();
      for (let j = c; j < c + k; j++) { seen.add(top[j]); seen.add(bottom[j]); }
      for (let i = r + 1; i < r + k - 1; i++) { seen.add(matrix[i][c]); seen.add(matrix[i][c + k - 1]); }
      let score = 0;
      for (const v of seen) score += v;
      if (best === null || score > best) best = score;
    }
  }
  return best;
}

function maxFrameDistinctSum(matrix, frameSize) { return solve(matrix, frameSize); }

module.exports = solve;
module.exports.maxFrameDistinctSum = maxFrameDistinctSum;
