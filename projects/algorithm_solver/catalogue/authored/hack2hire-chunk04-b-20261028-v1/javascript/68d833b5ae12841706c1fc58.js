"use strict";
// Hack2Hire 68d833b5ae12841706c1fc58 (Collatz Sequence Steps) over an INFERRED spec; qualification unknown.

function solve(n) {
  let steps = 0;
  while (n !== 1) {
    n = n % 2 === 1 ? 3 * n + 1 : n / 2;
    steps++;
  }
  return steps;
}

function collatzSteps(n) { return solve(n); }

module.exports = solve;
module.exports.collatzSteps = collatzSteps;
