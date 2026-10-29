// Original hack2hire:68fd2b2247bea664c0bba304; inferred public-preview contract; qualification unknown.
"use strict";
function distinctGoodnessValues(arr) {
  const tails = new Map([[0n,-1]]);
  for (const value of arr) for (const [mask,last] of [...tails]) if (last < value) {
    const combined = mask | BigInt(value);
    if (!tails.has(combined) || value < tails.get(combined)) tails.set(combined, value);
  }
  return [...tails.keys()].map(Number).sort((a,b) => a-b);
}

const solve = distinctGoodnessValues;
module.exports = solve;
module.exports.distinctGoodnessValues = distinctGoodnessValues;
module.exports.Solution = class { distinctGoodnessValues(...args) { return distinctGoodnessValues(...args); } };
