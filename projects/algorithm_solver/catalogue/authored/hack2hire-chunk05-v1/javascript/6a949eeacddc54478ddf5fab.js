// Original hack2hire:6a949eeacddc54478ddf5fab; inferred public-preview contract; qualification unknown.
"use strict";
function countGridSquares(queries) {
  return queries.map(([rows, cols]) => {
    const r = BigInt(rows), c = BigInt(cols), m = r < c ? r : c;
    return m * (r + 1n) * (c + 1n) - (r + c + 2n) * m * (m + 1n) / 2n + m * (m + 1n) * (2n * m + 1n) / 6n;
  });
}

const solve = countGridSquares;
module.exports = solve;
module.exports.countGridSquares = countGridSquares;
module.exports.Solution = class { countGridSquares(...args) { return countGridSquares(...args); } };
