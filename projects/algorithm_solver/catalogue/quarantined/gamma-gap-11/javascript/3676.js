'use strict';

// 3676. Count Bowl Subarrays.
// O(n) time and O(n) auxiliary space; inputs are preserved.
function solve(nums) {
  const stack = [];
  let answer = 0;
  for (let right = 0; right < nums.length; right += 1) {
    while (stack.length > 0 && nums[stack[stack.length - 1]] < nums[right]) {
      const left = stack.pop();
      if (right - left >= 2) answer += 1;
    }
    if (stack.length > 0 && right - stack[stack.length - 1] >= 2) answer += 1;
    stack.push(right);
  }
  return answer;
}

const bowlSubarrays = solve;
class Solution {
  bowlSubarrays(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, bowlSubarrays };
