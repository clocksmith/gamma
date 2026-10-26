'use strict';

// 2741. Special Permutations: count compatible permutations by used-index masks and their final index.
// O(n * n * 2^n) time and O(n * 2^n) auxiliary space; inputs are read-only.
function solve(nums) {
  const modulus = 1000000007;
  const size = nums.length;
  const compatible = new Int32Array(size);
  for (let left = 0; left < size; left += 1) {
    for (let right = 0; right < size; right += 1) {
      if (left !== right && (nums[left] % nums[right] === 0 || nums[right] % nums[left] === 0)) {
        compatible[left] |= 1 << right;
      }
    }
  }
  const ways = Array.from({ length: 1 << size }, () => new Int32Array(size));
  for (let index = 0; index < size; index += 1) ways[1 << index][index] = 1;
  for (let mask = 1; mask < ways.length; mask += 1) {
    for (let last = 0; last < size; last += 1) {
      const count = ways[mask][last];
      if (count === 0) continue;
      let remaining = compatible[last] & ~mask;
      while (remaining !== 0) {
        const bit = remaining & -remaining;
        const following = 31 - Math.clz32(bit);
        const target = mask | bit;
        ways[target][following] = (ways[target][following] + count) % modulus;
        remaining -= bit;
      }
    }
  }
  let result = 0;
  for (const count of ways[ways.length - 1]) result = (result + count) % modulus;
  return result;
}

const specialPerm = solve;
class Solution {
  specialPerm(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, specialPerm };
