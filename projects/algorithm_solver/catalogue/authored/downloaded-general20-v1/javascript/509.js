'use strict';

// 509. Fibonacci Number (Easy).
// Specification: https://leetcode.com/problems/fibonacci-number/description/
function solve(n) {
  if (n < 2) return n;
  let previous = 0;
  let current = 1;
  for (let step = 2; step <= n; step++) { const next = previous + current; previous = current; current = next; }
  return current;
}

const fib = solve;
class Solution {
  fib(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, fib };
