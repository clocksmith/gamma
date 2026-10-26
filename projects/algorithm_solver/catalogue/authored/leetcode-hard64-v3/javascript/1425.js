'use strict';

// 1425. Constrained Subsequence Sum: monotonic deque of DP maxima; O(n) time and O(n) space.

function solve(nums, k) {
  const best = Array(nums.length).fill(0);
  const queue = [];
  let head = 0;
  let answer = -Infinity;
  for (let index = 0; index < nums.length; index += 1) {
    while (head < queue.length && queue[head] < index - k) head += 1;
    best[index] = nums[index] + Math.max(0, head < queue.length ? best[queue[head]] : 0);
    answer = Math.max(answer, best[index]);
    while (queue.length > head && best[queue[queue.length - 1]] <= best[index]) queue.pop();
    queue.push(index);
  }
  return answer;
}

const constrainedSubsetSum = solve;
class Solution {
  constrainedSubsetSum(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, constrainedSubsetSum };
