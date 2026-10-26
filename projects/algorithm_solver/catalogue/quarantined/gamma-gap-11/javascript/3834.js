'use strict';

// 3834. Merge Adjacent Equal Elements.
// O(n) time and space; stack reductions implement leftmost-first merging without mutating inputs.
function solve(nums) {
  const stack = [];
  for (let value of nums) {
    while (stack.length > 0 && stack[stack.length - 1] === value) value += stack.pop();
    stack.push(value);
  }
  return stack;
}

const mergeAdjacent = solve;
class Solution {
  mergeAdjacent(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mergeAdjacent };
