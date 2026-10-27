'use strict';

// 3630. Partition Array for Maximum XOR and AND.
// Specification: https://leetcode.com/problems/partition-array-for-maximum-xor-and-and/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(2^n * n * 30) time, O(2^n + 30) space; n <= 19 and values < 2^30.
// Inputs are not modified.
// For fixed B, XOR(A) + XOR(C) = totalXor + 2 * (XOR(A) & ~totalXor); a projected linear basis maximizes the second term.

function solve(nums) {
  const size = 1 << nums.length, full = size - 1, xors = new Int32Array(size), ands = new Int32Array(size);
  for (let subset = 1; subset < size; subset++) {
    const bit = subset & -subset, value = nums[31 - Math.clz32(bit)], rest = subset ^ bit;
    xors[subset] = xors[rest] ^ value;
    ands[subset] = rest ? ands[rest] & value : value;
  }
  let answer = 0;
  for (let remaining = 0; remaining < size; remaining++) {
    const totalXor = xors[remaining], basis = new Int32Array(30);
    let bits = remaining;
    while (bits) {
      const bit = bits & -bits; bits ^= bit;
      let value = nums[31 - Math.clz32(bit)] & ~totalXor;
      while (value) {
        const leading = 31 - Math.clz32(value);
        if (basis[leading]) value ^= basis[leading];
        else { basis[leading] = value; break; }
      }
    }
    let best = 0;
    for (let bit = 29; bit >= 0; bit--) best = Math.max(best, best ^ basis[bit]);
    answer = Math.max(answer, ands[full ^ remaining] + totalXor + 2 * best);
  }
  return answer;
}

const maximizeXorAndXor = solve;
class Solution {
  maximizeXorAndXor(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximizeXorAndXor };
