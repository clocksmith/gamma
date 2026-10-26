'use strict';

// 3040. Maximum Number of Operations With the Same Score II: evaluate the three possible scores with rolling interval-DP diagonals.
// O(n * n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const size = nums.length;
  const scores = new Set([nums[0] + nums[1], nums[size - 2] + nums[size - 1], nums[0] + nums[size - 1]]);
  let best = 0;
  for (const score of scores) {
    let previous = new Int32Array(size + 1);
    for (let length = 2 + size % 2; length <= size; length += 2) {
      const current = new Int32Array(size - length + 1);
      for (let left = 0; left + length <= size; left += 1) {
        const right = left + length - 1;
        let count = 0;
        if (nums[left] + nums[left + 1] === score) count = Math.max(count, 1 + previous[left + 2]);
        if (nums[left] + nums[right] === score) count = Math.max(count, 1 + previous[left + 1]);
        if (nums[right - 1] + nums[right] === score) count = Math.max(count, 1 + previous[left]);
        current[left] = count;
      }
      previous = current;
    }
    best = Math.max(best, previous[0]);
  }
  return best;
}

const maxOperations = solve;
class Solution {
  maxOperations(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxOperations };
