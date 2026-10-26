'use strict';

// 3670. Maximum Product of Two Integers With No Common Bits.
// O(n + B * 2^B) time and O(2^B) auxiliary space; B <= 20. Inputs are preserved.
function solve(nums) {
  let maximum = 0;
  for (const value of nums) maximum = Math.max(maximum, value);
  let size = 1;
  while (size <= maximum) size *= 2;
  const best = new Int32Array(size);
  for (const value of nums) best[value] = value;
  for (let bit = 1; bit < size; bit *= 2) {
    for (let start = 0; start < size; start += 2 * bit) {
      for (let offset = 0; offset < bit; offset += 1) {
        const index = start + bit + offset;
        best[index] = Math.max(best[index], best[index - bit]);
      }
    }
  }
  const mask = size - 1;
  let answer = 0;
  for (const value of nums) answer = Math.max(answer, value * best[mask ^ value]);
  return answer;
}

const maxProduct = solve;
class Solution {
  maxProduct(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxProduct };
