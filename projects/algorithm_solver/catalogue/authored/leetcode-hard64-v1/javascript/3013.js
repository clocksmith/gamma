'use strict';

// 3013. Divide an Array Into Subarrays With Minimum Cost II: sliding order statistics with count and sum Fenwick trees.
// O(n log n) time and O(n) auxiliary space. Inputs are preserved.
function solve(nums, k, dist) {
  const coordinates = Array.from(new Set(nums.slice(1))).sort((a, b) => a - b);
  const size = coordinates.length;
  const counts = new Int32Array(size + 1);
  const sums = new Float64Array(size + 1);
  function update(value, change) {
    let left = 0;
    let right = size;
    while (left < right) {
      const middle = Math.floor((left + right) / 2);
      if (coordinates[middle] < value) left = middle + 1;
      else right = middle;
    }
    for (let index = left + 1; index <= size; index += index & -index) {
      counts[index] += change;
      sums[index] += change * value;
    }
  }
  function smallestSum(amount) {
    let index = 0;
    let total = 0;
    let step = 1;
    while (step * 2 <= size) step *= 2;
    for (; step >= 1; step = Math.floor(step / 2)) {
      const following = index + step;
      if (following <= size && counts[following] < amount) {
        amount -= counts[following];
        total += sums[following];
        index = following;
      }
    }
    return total + amount * coordinates[index];
  }
  for (let index = 1; index <= dist + 1; index += 1) update(nums[index], 1);
  let best = smallestSum(k - 1);
  for (let right = dist + 2; right < nums.length; right += 1) {
    update(nums[right - dist - 1], -1);
    update(nums[right], 1);
    best = Math.min(best, smallestSum(k - 1));
  }
  return nums[0] + best;
}

const minimumCost = solve;
class Solution {
  minimumCost(nums, k, dist) { return solve(nums, k, dist); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumCost };
