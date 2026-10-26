'use strict';

// 1673. Find the Most Competitive Subsequence: spend the deletion budget on larger preceding values.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums, k) {
  let remaining = nums.length - k;
  const stack = [];
  for (const value of nums) {
    while (remaining > 0 && stack.length && stack[stack.length - 1] > value) {
      stack.pop();
      remaining -= 1;
    }
    stack.push(value);
  }
  return stack.slice(0, k);
}

const mostCompetitive = solve;
class Solution {
  mostCompetitive(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mostCompetitive };
