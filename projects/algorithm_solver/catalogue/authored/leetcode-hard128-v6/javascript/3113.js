'use strict';

// 3113. Find the Number of Subarrays Where Boundary Elements Are Maximum.
// A decreasing stack groups still-visible equal maxima; O(n) time and space. Inputs are preserved.

function solve(nums) {
  const stack = [];
  let answer = 0;
  for (const value of nums) {
    while (stack.length > 0 && stack[stack.length - 1][0] < value) stack.pop();
    if (stack.length > 0 && stack[stack.length - 1][0] === value) stack[stack.length - 1][1] += 1;
    else stack.push([value, 1]);
    answer += stack[stack.length - 1][1];
  }
  return answer;
}

const numberOfSubarrays = solve;
class Solution {
  numberOfSubarrays(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfSubarrays };
