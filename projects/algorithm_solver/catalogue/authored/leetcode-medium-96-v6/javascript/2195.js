'use strict';

// 2195. Append K Integers With Minimal Sum: fill missing positive-integer gaps using exact arithmetic-series sums.
// O(n log n) time and O(n) auxiliary space on the stated integer domain; inputs are read-only.
function solve(nums, k) {
  const ordered = Array.from(new Set(nums)).sort((left, right) => left - right);
  let remaining = k;
  let current = 1;
  let total = 0n;
  function series(start, count) {
    const amount = BigInt(count);
    return amount * (2n * BigInt(start) + amount - 1n) / 2n;
  }
  for (const value of ordered) {
    if (value < current) continue;
    const take = Math.min(remaining, value - current);
    total += series(current, take);
    remaining -= take;
    if (remaining === 0) return Number(total);
    current = value + 1;
  }
  total += series(current, remaining);
  // The stated n and k bounds keep the final answer within Number's exact range.
  return Number(total);
}

const minimalKSum = solve;
class Solution {
  minimalKSum(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimalKSum };
