'use strict';

// 3007. Maximum Number That Sum of the Prices Is Less Than or Equal to K: binary search cumulative selected-bit counts using exact integers.
// O(log^2(k + 2)) bounded integer operations and O(1) auxiliary variables; inputs are read-only.
function solve(k, x) {
  if (typeof k !== 'bigint' && !Number.isSafeInteger(k)) throw new RangeError('k must be an exact integer');
  const budget = BigInt(k);
  const spacing = BigInt(x);
  function price(limit) {
    const count = limit + 1n;
    let total = 0n;
    for (let bit = 1n << (spacing - 1n); bit <= limit; bit <<= spacing) {
      const cycle = bit * 2n;
      const remainder = count % cycle;
      total += count / cycle * bit + (remainder > bit ? remainder - bit : 0n);
      if (total > budget) return total;
    }
    return total;
  }
  let low = 0n;
  let high = (budget + 1n) << spacing;
  while (low + 1n < high) {
    const middle = (low + high) / 2n;
    if (price(middle) <= budget) low = middle;
    else high = middle;
  }
  const answer = Number(low);
  if (!Number.isSafeInteger(answer)) throw new RangeError('result exceeds the Number return domain');
  return answer;
}

const findMaximumNumber = solve;
class Solution {
  findMaximumNumber(k, x) { return solve(k, x); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaximumNumber };
