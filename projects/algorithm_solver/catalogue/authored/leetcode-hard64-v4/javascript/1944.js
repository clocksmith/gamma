'use strict';

// 1944. Number of Visible People in a Queue. Decreasing stack for the problem's distinct heights; O(n) time and O(n) space. Inputs are preserved.

function solve(heights) {
  const answer = Array(heights.length).fill(0);
  const stack = [];
  for (let index = heights.length - 1; index >= 0; index -= 1) {
    while (stack.length > 0 && stack[stack.length - 1] < heights[index]) {
      stack.pop();
      answer[index] += 1;
    }
    if (stack.length > 0) answer[index] += 1;
    stack.push(heights[index]);
  }
  return answer;
}

const canSeePersonsCount = solve;
class Solution {
  canSeePersonsCount(heights) { return solve(heights); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canSeePersonsCount };
