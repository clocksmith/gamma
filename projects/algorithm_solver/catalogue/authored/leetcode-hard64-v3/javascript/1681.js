'use strict';

// 1681. Minimum Incompatibility: valid-group masks with first-unused-index symmetry breaking; O(3^n+n*2^n) time and O(2^n) space.

function solve(nums, k) {
  const size = nums.length;
  const groupSize = size / k;
  const frequency = new Map();
  for (const value of nums) {
    const count = (frequency.get(value) || 0) + 1;
    if (count > k) return -1;
    frequency.set(value, count);
  }
  const limit = 1 << size;
  const groups = Array.from({ length: size }, () => []);
  for (let mask = 1; mask < limit; mask += 1) {
    let count = 0;
    for (let bits = mask; bits !== 0; bits &= bits - 1) count += 1;
    if (count !== groupSize) continue;
    const values = new Set();
    let low = Infinity;
    let high = -Infinity;
    for (let index = 0; index < size; index += 1) {
      if ((mask & (1 << index)) !== 0) {
        values.add(nums[index]);
        low = Math.min(low, nums[index]);
        high = Math.max(high, nums[index]);
      }
    }
    if (values.size !== groupSize) continue;
    const first = 31 - Math.clz32(mask & -mask);
    groups[first].push([mask, high - low]);
  }
  const best = Array(limit).fill(Infinity);
  best[0] = 0;
  const full = limit - 1;
  for (let used = 0; used < full; used += 1) {
    if (best[used] === Infinity) continue;
    const available = full ^ used;
    const first = 31 - Math.clz32(available & -available);
    for (const [mask, price] of groups[first]) {
      if ((mask & used) === 0) {
        const following = mask | used;
        best[following] = Math.min(best[following], best[used] + price);
      }
    }
  }
  return best[full] === Infinity ? -1 : best[full];
}

const minimumIncompatibility = solve;
class Solution {
  minimumIncompatibility(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumIncompatibility };
