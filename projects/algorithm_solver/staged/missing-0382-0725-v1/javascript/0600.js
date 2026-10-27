'use strict';

// 600. Non-negative Integers without Consecutive Ones. Binary digit counting with Fibonacci suffix counts, including zero.

function solve(n) {
  const length = n.toString(2).length, counts = [1, 2];
  for (let i = 2; i <= length; i += 1) counts.push(counts[i - 1] + counts[i - 2]);
  let answer = 0, previous = 0;
  for (let bit = length - 1; bit >= 0; bit -= 1) {
    if ((n & (1 << bit)) !== 0) {
      answer += counts[bit];
      if (previous) return answer;
      previous = 1;
    } else previous = 0;
  }
  return answer + 1;
}

const findIntegers = solve;
class Solution {
  findIntegers(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findIntegers };
