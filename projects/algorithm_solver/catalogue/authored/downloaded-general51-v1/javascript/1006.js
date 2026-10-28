'use strict';

// 1006. Clumsy Factorial (Medium).
// Specification: https://leetcode.com/problems/clumsy-factorial/description/
function solve(n) {
  const stack = [n];
  let index = n - 1;
  let operation = 0;
  while (index > 0) {
    if (operation === 0) stack.push(stack.pop() * index);
    else if (operation === 1) stack.push(Math.trunc(stack.pop() / index));
    else if (operation === 2) stack.push(index);
    else stack.push(-index);
    operation = (operation + 1) % 4;
    index--;
  }
  return stack.reduce((sum, value) => sum + value, 0);
}
const clumsy = solve;
class Solution { clumsy(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, clumsy };
