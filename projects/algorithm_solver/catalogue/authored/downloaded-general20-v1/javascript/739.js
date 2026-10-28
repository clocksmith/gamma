'use strict';

// 739. Daily Temperatures (Medium).
// Specification: https://leetcode.com/problems/daily-temperatures/description/
function solve(temperatures) {
  const answer = new Array(temperatures.length).fill(0);
  const stack = [];
  for (let index = 0; index < temperatures.length; index++) {
    while (stack.length > 0 && temperatures[stack[stack.length - 1]] < temperatures[index]) {
      const previous = stack.pop();
      answer[previous] = index - previous;
    }
    stack.push(index);
  }
  return answer;
}

const dailyTemperatures = solve;
class Solution {
  dailyTemperatures(temperatures) { return solve(temperatures); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, dailyTemperatures };
