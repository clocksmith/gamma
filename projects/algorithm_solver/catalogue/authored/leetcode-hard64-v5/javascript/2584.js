'use strict';

// 2584. Split the Array to Make Coprime Products. Join the first and last occurrence intervals of each prime factor; O(M log log(M+2)+n log(M+1)) time and O(M+n) space, M=max(nums). Inputs are preserved.

function solve(nums) {
  let maximum = 0;
  for (const value of nums) maximum = Math.max(maximum, value);
  const smallest = Array(maximum + 1).fill(0);
  for (let prime = 2; prime * prime <= maximum; prime += 1) {
    if (smallest[prime] !== 0) continue;
    for (let multiple = prime * prime; multiple <= maximum; multiple += prime) {
      if (smallest[multiple] === 0) smallest[multiple] = prime;
    }
  }
  const first = new Map();
  const reach = Array.from({ length: nums.length }, (_, index) => index);
  for (let index = 0; index < nums.length; index += 1) {
    let value = nums[index];
    while (value > 1) {
      const factor = smallest[value] || value;
      if (!first.has(factor)) first.set(factor, index);
      reach[first.get(factor)] = index;
      while (value % factor === 0) value /= factor;
    }
  }
  let end = 0;
  for (let index = 0; index + 1 < nums.length; index += 1) {
    end = Math.max(end, reach[index]);
    if (end === index) return index;
  }
  return -1;
}

const findValidSplit = solve;
class Solution {
  findValidSplit(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findValidSplit };
