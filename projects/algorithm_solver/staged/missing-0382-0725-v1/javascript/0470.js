'use strict';

// 470. Implement Rand10() Using Rand7().

function solve(rand7Api) {
  const draw = rand7Api === undefined ? rand7 : rand7Api;
  while (true) {
    const value = (draw() - 1) * 7 + draw() - 1;
    if (value < 40) return value % 10 + 1;
  }
}
const rand10 = solve;
class Solution { rand10() { return solve(); } }

if (typeof module !== 'undefined') module.exports = { solve, Solution, rand10 };
