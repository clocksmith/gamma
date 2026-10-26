'use strict';

// 412. Fizz Buzz (Easy).
// Specification: https://leetcode.com/problems/fizz-buzz/description/
// O(n log n) character output in general; fresh output strings for integers 1 through n.
function solve(n) {
  const result = [];
  for (let value = 1; value <= n; value++) {
    let word = '';
    if (value % 3 === 0) word += 'Fizz';
    if (value % 5 === 0) word += 'Buzz';
    result.push(word || String(value));
  }
  return result;
}

const fizzBuzz = solve;
class Solution {
  fizzBuzz(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, fizzBuzz };
