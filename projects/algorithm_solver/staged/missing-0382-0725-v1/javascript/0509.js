'use strict';

// 509. Fibonacci Number.

function solve(n) {
  let a = 0, b = 1;
  for (let i = 0; i < n; i += 1) [a, b] = [b, a + b];
  return a;
}

const fib = solve;
class Solution {
  fib(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, fib };
