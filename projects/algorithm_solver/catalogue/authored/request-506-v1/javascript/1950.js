// Original candidate. Contract: https://leetcode.com/problems/maximum-of-minimum-values-in-all-subarrays/
"use strict";

function solve(nums) {
  const n = nums.length;
  const stack = [];
  const answer = Array(n).fill(0);

  // Popping an index closes the largest span for which it is a minimum.
  for (let right = 0; right <= n; right++) {
    while (stack.length &&
           (right === n || nums[stack[stack.length - 1]] >= nums[right])) {
      const index = stack.pop();
      const left = stack.length ? stack[stack.length - 1] : -1;
      const length = right - left - 1;
      answer[length - 1] = Math.max(answer[length - 1], nums[index]);
    }
    stack.push(right);
  }

  // A minimum attainable for a longer window also bounds a shorter one.
  for (let i = n - 2; i >= 0; i--) {
    answer[i] = Math.max(answer[i], answer[i + 1]);
  }
  return answer;
}

module.exports = solve;
