'use strict';

// 4054. Count Shadow Pairs I.
// Specification: https://leetcode.com/problems/count-shadow-pairs-i/description/
// O(n) time and space; active prefix minima grouped by equal value. Inputs are preserved.
function solve(nums) {
  const stack = [];
  let active = 0, answer = 0;
  for (const value of nums) {
    while (stack.length && stack[stack.length - 1][0] > value) active -= stack.pop()[1];
    const equal = stack.length && stack[stack.length - 1][0] === value ? stack[stack.length - 1][1] : 0;
    answer += active - equal;
    if (equal) stack[stack.length - 1][1]++;
    else stack.push([value, 1]);
    active++;
  }
  return answer;
}

// Native judge method name is not established; canonical solve is the supported entry point.
if (typeof module !== 'undefined') module.exports = { solve };
