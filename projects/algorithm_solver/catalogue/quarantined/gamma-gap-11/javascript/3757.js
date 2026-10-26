'use strict';

// 3757. Number of Effective Subsequences.
// O(n + B * 2^B) time and O(n + 2^B) space, B <= 20; subset zeta counts plus inclusion-exclusion.
function solve(nums) {
  const modulus = 1000000007;
  let full = 0;
  for (const value of nums) full |= value;
  let width = 0;
  while (2 ** width <= full) width += 1;
  const size = 2 ** width;
  const subsetCount = new Int32Array(size);
  for (const value of nums) subsetCount[value] += 1;
  for (let bit = 0; bit < width; bit += 1) {
    const step = 2 ** bit;
    for (let base = 0; base < size; base += 2 * step) {
      for (let offset = 0; offset < step; offset += 1) subsetCount[base + step + offset] += subsetCount[base + offset];
    }
  }
  const powers = new Float64Array(nums.length + 1);
  powers[0] = 1;
  for (let index = 0; index < nums.length; index += 1) powers[index + 1] = powers[index] * 2 % modulus;
  let exactFull = 0;
  let mask = full;
  while (true) {
    let missing = full ^ mask;
    let parity = 0;
    while (missing !== 0) {
      parity ^= 1;
      missing &= missing - 1;
    }
    const term = powers[subsetCount[mask]];
    exactFull = (exactFull + (parity ? -term : term) + modulus) % modulus;
    if (mask === 0) break;
    mask = (mask - 1) & full;
  }
  return (powers[nums.length] - exactFull + modulus) % modulus;
}

const countEffective = solve;
class Solution {
  countEffective(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countEffective };
