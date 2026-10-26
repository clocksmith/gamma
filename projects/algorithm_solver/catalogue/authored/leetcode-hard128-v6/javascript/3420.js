'use strict';

// 3420. Count Non-Decreasing Subarrays After K Operations.
// A reverse sliding window maintains raised plateaus in a monotonic deque; O(n) time and O(n) space. Inputs are preserved.

function solve(nums, k) {
  const plateaus = [];
  let head = 0, right = nums.length - 1, cost = 0, answer = 0;
  for (let left = nums.length - 1; left >= 0; left -= 1) {
    while (plateaus.length > head && nums[plateaus[plateaus.length - 1]] < nums[left]) {
      const index = plateaus.pop();
      const boundary = plateaus.length > head ? plateaus[plateaus.length - 1] : right + 1;
      cost += (boundary - index) * (nums[left] - nums[index]);
    }
    plateaus.push(left);
    while (cost > k) {
      cost -= nums[plateaus[head]] - nums[right];
      if (plateaus[head] === right) head += 1;
      right -= 1;
    }
    answer += right - left + 1;
  }
  return answer;
}

const countNonDecreasingSubarrays = solve;
class Solution {
  countNonDecreasingSubarrays(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countNonDecreasingSubarrays };
