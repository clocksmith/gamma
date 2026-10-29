"use strict";
// Hack2Hire 6a226625981072682a6f216b (Matrix Transpose with Workers); INFERRED spec, workers simulated deterministically; qualification unknown.
function solve(matrix, numThreads) {
  const n = matrix.length, workers = Math.min(numThreads, n), out = new Array(n);
  const base = Math.floor(n / workers), extra = n % workers;
  let start = 0;
  for (let w = 0; w < workers; w++) {  // each simulated worker owns a contiguous block of output rows
    const stop = start + base + (w < extra ? 1 : 0);
    for (let j = start; j < stop; j++) { const row = new Array(n); for (let i = 0; i < n; i++) row[i] = matrix[i][j]; out[j] = row; }
    start = stop;
  }
  return out;
}
function transposeWithWorkers(matrix, numThreads) { return solve(matrix, numThreads); }
module.exports = solve;
module.exports.transposeWithWorkers = transposeWithWorkers;
