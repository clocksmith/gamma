'use strict';

// 2169. Count Operations to Obtain Zero (Easy).
// Specification: https://leetcode.com/problems/count-operations-to-obtain-zero/description/
// O(log(max(num1, num2) + 1)) time, O(1) space; batch repeated subtractions by quotient.
function solve(num1, num2) {
  let first = num1;
  let second = num2;
  let operations = 0;
  while (first > 0 && second > 0) {
    if (first < second) [first, second] = [second, first];
    operations += Math.floor(first / second);
    first %= second;
  }
  return operations;
}

const countOperations = solve;
class Solution {
  countOperations(num1, num2) { return solve(num1, num2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countOperations };
