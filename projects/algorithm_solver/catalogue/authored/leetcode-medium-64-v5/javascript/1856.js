'use strict';

// 1856. Maximum Subarray Min-Product: use increasing minima and prefix sums to evaluate each maximal span.
// O(n) time and O(n) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(nums) {
  const prefix = [0];
  for (const value of nums) prefix.push(prefix[prefix.length - 1] + value);
  const stack = [];
  let best = 0n;
  for (let right = 0; right <= nums.length; right += 1) {
    const value = right < nums.length ? nums[right] : 0;
    while (stack.length && nums[stack[stack.length - 1]] > value) {
      const minimum = nums[stack.pop()];
      const left = stack.length ? stack[stack.length - 1] + 1 : 0;
      // Sums fit Number exactly, but the product can exceed its integer range.
      const product = BigInt(minimum) * BigInt(prefix[right] - prefix[left]);
      if (product > best) best = product;
    }
    if (right < nums.length) stack.push(right);
  }
  return Number(best % 1000000007n);
}

const maxSumMinProduct = solve;
class Solution {
  maxSumMinProduct(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSumMinProduct };
