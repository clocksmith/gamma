// Original hack2hire:6927c1a99c0536c47b291ab5; inferred public-preview contract; qualification unknown.
"use strict";
function distinctPrimeProducts(primes) {
  const values = new Set([1n]);
  for (const prime of primes) for (const value of [...values]) values.add(value * BigInt(prime));
  values.delete(1n);
  return [...values].sort((a,b) => a < b ? -1 : a > b ? 1 : 0);
}

const solve = distinctPrimeProducts;
module.exports = solve;
module.exports.distinctPrimeProducts = distinctPrimeProducts;
module.exports.Solution = class { distinctPrimeProducts(...args) { return distinctPrimeProducts(...args); } };
