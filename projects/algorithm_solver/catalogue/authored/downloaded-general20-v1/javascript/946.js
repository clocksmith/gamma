'use strict';

// 946. Validate Stack Sequences (Medium).
// Specification: https://leetcode.com/problems/validate-stack-sequences/description/
function solve(pushed, popped) {
  const stack = [];
  let poppedIndex = 0;
  for (const value of pushed) {
    stack.push(value);
    while (stack.length > 0 && poppedIndex < popped.length && stack[stack.length - 1] === popped[poppedIndex]) {
      stack.pop();
      poppedIndex++;
    }
  }
  return stack.length === 0;
}

const validateStackSequences = solve;
class Solution {
  validateStackSequences(pushed, popped) { return solve(pushed, popped); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, validateStackSequences };
