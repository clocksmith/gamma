'use strict';

// 719. Find K-th Smallest Pair Distance.

function solve(nums, k) {
  const ordered = nums.slice().sort((a, b) => a - b);
  let low = 0, high = ordered[ordered.length - 1] - ordered[0];
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    let left = 0, count = 0;
    for (let right = 0; right < ordered.length; right += 1) {
      while (ordered[right] - ordered[left] > middle) left += 1;
      count += right - left;
    }
    if (count >= k) high = middle; else low = middle + 1;
  }
  return low;
}

const smallestDistancePair = solve;
class Solution {
  smallestDistancePair(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestDistancePair };
