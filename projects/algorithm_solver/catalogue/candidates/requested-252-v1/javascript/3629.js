'use strict';

// 3629. Minimum Jumps to Reach End via Prime Teleportation.
// Specification: https://leetcode.com/problems/minimum-jumps-to-reach-end-via-prime-teleportation/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(V log log V + n log V) time, O(V + n log V) space; expand each prime teleport bucket once.
// Inputs are not modified.

function solve(nums) {
  let maximum = 0;
  for (const value of nums) maximum = Math.max(maximum, value);
  const smallest = Int32Array.from({ length: maximum + 1 }, (_, value) => value);
  for (let value = 2; value * value <= maximum; value++) if (smallest[value] === value) {
    for (let multiple = value * value; multiple <= maximum; multiple += value) if (smallest[multiple] === multiple) smallest[multiple] = value;
  }
  const buckets = new Map();
  for (let index = 0; index < nums.length; index++) {
    let remaining = nums[index];
    while (remaining > 1) {
      const factor = smallest[remaining];
      if (!buckets.has(factor)) buckets.set(factor, []);
      buckets.get(factor).push(index);
      while (remaining % factor === 0) remaining /= factor;
    }
  }
  const distance = new Int32Array(nums.length).fill(-1), queue = [0]; distance[0] = 0;
  for (let head = 0; head < queue.length; head++) {
    const index = queue[head];
    if (index === nums.length - 1) return distance[index];
    const candidates = [];
    if (index > 0) candidates.push(index - 1);
    if (index + 1 < nums.length) candidates.push(index + 1);
    const value = nums[index];
    if (value >= 2 && smallest[value] === value) {
      const extra = buckets.get(value) || [];
      for (const target of extra) candidates.push(target);
      buckets.delete(value);
    }
    for (const target of candidates) if (distance[target] < 0) { distance[target] = distance[index] + 1; queue.push(target); }
  }
  return -1;
}

const minJumps = solve;
class Solution {
  minJumps(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minJumps };
