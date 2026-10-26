'use strict';

// 1703. Minimum Adjacent Swaps for K Consecutive Ones: normalized one-positions and sliding medians; O(n) time and O(n) space.

function solve(nums, k) {
  const positions = [];
  for (let index = 0; index < nums.length; index += 1) {
    if (nums[index] === 1) positions.push(index - positions.length);
  }
  const prefix = Array(positions.length + 1).fill(0);
  for (let index = 0; index < positions.length; index += 1) prefix[index + 1] = prefix[index] + positions[index];
  let answer = Infinity;
  for (let left = 0; left + k <= positions.length; left += 1) {
    const right = left + k;
    const middle = left + Math.floor(k / 2);
    const median = positions[middle];
    let cost = median * (middle - left) - (prefix[middle] - prefix[left]);
    cost += prefix[right] - prefix[middle + 1] - median * (right - middle - 1);
    answer = Math.min(answer, cost);
  }
  return answer;
}

const minMoves = solve;
class Solution {
  minMoves(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMoves };
