'use strict';

// 2680. Maximum OR: combine prefix and suffix ORs with all shifts on one element.
// O(n) time and O(n) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(nums, k) {
  const suffix = new Int32Array(nums.length + 1);
  for (let index = nums.length - 1; index >= 0; index -= 1) suffix[index] = suffix[index + 1] | nums[index];
  const shift = BigInt(k);
  let prefix = 0;
  let best = 0n;
  for (let index = 0; index < nums.length; index += 1) {
    const value = BigInt(prefix) | (BigInt(nums[index]) << shift) | BigInt(suffix[index + 1]);
    if (value > best) best = value;
    prefix |= nums[index];
  }
  // The stated nums <= 1e9 and k <= 15 bound keeps the result below 2^45.
  return Number(best);
}

const maximumOr = solve;
class Solution {
  maximumOr(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumOr };
