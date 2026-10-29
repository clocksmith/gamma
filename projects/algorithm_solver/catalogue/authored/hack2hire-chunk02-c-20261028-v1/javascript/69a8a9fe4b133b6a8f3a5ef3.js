"use strict";
// Hack2Hire 69a8a9fe4b133b6a8f3a5ef3 (Crypto Block Mining, variant 1) over an INFERRED spec; qualification unknown.
function solve(transactions, blockSize) {
  const best = new Float64Array(blockSize + 1);
  for (const [, size, fee] of transactions) {
    for (let capacity = blockSize; capacity >= size; capacity--) {
      const candidate = best[capacity - size] + fee;
      if (candidate > best[capacity]) best[capacity] = candidate;
    }
  }
  return best[blockSize];
}
function maxFees(transactions, blockSize) { return solve(transactions, blockSize); }
module.exports = solve;
module.exports.maxFees = maxFees;
