// Original implementation. Contract: https://leetcode.com/problems/number-of-ways-to-reach-destination-in-the-grid/
"use strict";

function solve(n, m, k, source, dest) {
  const rows = BigInt(n);
  const columns = BigInt(m);
  const MOD = 1000000007n;
  // Aggregate counts: destination, same row only, same column only, neither.
  let state = [0n, 0n, 0n, 0n];
  const sameRow = source[0] === dest[0];
  const sameColumn = source[1] === dest[1];
  state[sameRow && sameColumn ? 0 : sameRow ? 1 : sameColumn ? 2 : 3] = 1n;
  for (let step = 0; step < k; step++) {
    const [both, row, column, neither] = state;
    state = [
      (row + column) % MOD,
      ((columns - 1n) * both + (columns - 2n) * row + neither) % MOD,
      ((rows - 1n) * both + (rows - 2n) * column + neither) % MOD,
      ((rows - 1n) * row + (columns - 1n) * column + (rows + columns - 4n) * neither) % MOD,
    ];
  }
  return Number(state[0]);
}

module.exports = solve;
