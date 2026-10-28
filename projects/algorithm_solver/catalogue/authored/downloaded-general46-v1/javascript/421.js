'use strict';

// 421. Maximum XOR of Two Numbers in an Array (Medium).
// Specification: https://leetcode.com/problems/maximum-xor-of-two-numbers-in-an-array/description/
function solve(nums) {
  let maxXor = 0; let mask = 0;
  for (let bit = 30; bit >= 0; bit--) {
    mask |= (1 << bit);
    const prefixes = new Set(nums.map((value) => value & mask));
    const candidate = maxXor | (1 << bit);
    let found = false;
    for (const prefix of prefixes) { if (prefixes.has(prefix ^ candidate)) { found = true; break; } }
    if (found) maxXor = candidate;
  }
  return maxXor;
}
const findMaximumXOR = solve;
class Solution { findMaximumXOR(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaximumXOR };
