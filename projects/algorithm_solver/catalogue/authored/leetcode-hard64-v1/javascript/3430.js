'use strict';

// 3430. Maximum and Minimum Sums of at Most Size K Subarrays: monotonic-stack contributions with a truncated rectangle count.
// O(n) time and O(n) auxiliary space. Inputs are preserved.
function solve(nums, k) {
  const n = nums.length;
  function contributions(minimum) {
    const stack = [];
    let total = 0;
    for (let right = 0; right <= n; right += 1) {
      while (stack.length > 0 && (right === n || (minimum
        ? nums[stack[stack.length - 1]] >= nums[right]
        : nums[stack[stack.length - 1]] <= nums[right]))) {
        const middle = stack.pop();
        const previous = stack.length > 0 ? stack[stack.length - 1] : -1;
        const leftChoices = Math.min(k, middle - previous);
        const rightChoices = Math.min(k, right - middle);
        const excess = Math.max(0, leftChoices + rightChoices - k - 1);
        const count = leftChoices * rightChoices - excess * (excess + 1) / 2;
        total += nums[middle] * count;
      }
      if (right < n) stack.push(right);
    }
    return total;
  }
  // The official n<=80000 and |nums[i]|<=1e6 keep the total below 2^53.
  return contributions(true) + contributions(false);
}

const minMaxSubarraySum = solve;
class Solution {
  minMaxSubarraySum(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMaxSubarraySum };
