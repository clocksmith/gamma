"use strict";
// Hack2Hire 69a8acc74b133b6a8f3a5efd (Crypto Block Mining, variant 2) over an INFERRED spec; qualification unknown.
const SIZE_SCALE = 8192; // key = fee * SIZE_SCALE - size; exact below 2**53 for fees <= 1e8
function solve(transactions, blockSize) {
  const n = transactions.length, best = [];
  for (let i = 0; i <= n; i++) best.push(new Float64Array(blockSize + 1));
  for (let i = n - 1; i >= 0; i--) {
    const [, size, fee] = transactions[i], key = fee * SIZE_SCALE - size, here = best[i], after = best[i + 1];
    for (let capacity = 0; capacity <= blockSize; capacity++) {
      let value = after[capacity];
      if (size <= capacity && after[capacity - size] + key > value) value = after[capacity - size] + key;
      here[capacity] = value;
    }
  }
  const chosen = [];
  let capacity = blockSize;
  for (let i = 0; i < n; i++) {
    const [id, size, fee] = transactions[i];
    if (size <= capacity && best[i + 1][capacity - size] + fee * SIZE_SCALE - size === best[i][capacity]) {
      chosen.push(id);
      capacity -= size;
    }
  }
  return chosen;
}
function selectTransactions(transactions, blockSize) { return solve(transactions, blockSize); }
module.exports = solve;
module.exports.selectTransactions = selectTransactions;
