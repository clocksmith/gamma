'use strict';

// 3533. Concatenated Divisibility.
// Memoize subset/remainder feasibility and reconstruct by trying unused values in numeric order; O(n*k*2^n) time and O(k*2^n+n) space. Inputs are preserved.

function solve(nums, k) {
  const values = nums.slice().sort((a, b) => a - b);
  if (k === 1) return values;
  const n = values.length, full = (1 << n) - 1, memo = new Uint8Array((1 << n) * k);
  const factors = values.map(value => 10 ** String(value).length % k);
  function possible(mask, remainder) {
    if (mask === full) return remainder === 0;
    const identity = mask * k + remainder;
    if (memo[identity]) return memo[identity] === 2;
    for (let index = 0; index < n; index += 1) {
      if (mask & (1 << index)) continue;
      const following = (remainder * factors[index] + values[index]) % k;
      if (possible(mask | (1 << index), following)) { memo[identity] = 2; return true; }
    }
    memo[identity] = 1;
    return false;
  }
  if (!possible(0, 0)) return [];
  const answer = [];
  let mask = 0, remainder = 0;
  while (mask !== full) {
    for (let index = 0; index < n; index += 1) {
      if (mask & (1 << index)) continue;
      const following = (remainder * factors[index] + values[index]) % k;
      if (possible(mask | (1 << index), following)) {
        answer.push(values[index]); mask |= 1 << index; remainder = following; break;
      }
    }
  }
  return answer;
}

const concatenatedDivisibility = solve;
class Solution {
  concatenatedDivisibility(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, concatenatedDivisibility };
