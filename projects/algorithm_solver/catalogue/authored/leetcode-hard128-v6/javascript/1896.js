'use strict';

// 1896. Minimum Cost to Change the Final Value of Expression.
// Iterative expression reduction with costs for both Boolean outcomes; O(n) time and space. AND and OR have equal precedence.

function solve(expression) {
  const values = [], operators = [];
  function apply() {
    const operator = operators.pop(), right = values.pop(), left = values.pop(), cost = [Infinity, Infinity];
    for (let first = 0; first <= 1; first += 1) {
      for (let second = 0; second <= 1; second += 1) {
        for (const chosen of ['&', '|']) {
          const result = chosen === '&' ? first & second : first | second;
          cost[result] = Math.min(cost[result], left[first] + right[second] + Number(chosen !== operator));
        }
      }
    }
    values.push(cost);
  }
  for (const char of expression) {
    if (char === '0' || char === '1') values.push([Number(char), 1 - Number(char)]);
    else if (char === '(') operators.push(char);
    else if (char === ')') {
      while (operators[operators.length - 1] !== '(') apply();
      operators.pop();
    } else {
      while (operators.length > 0 && operators[operators.length - 1] !== '(') apply();
      operators.push(char);
    }
  }
  while (operators.length > 0) apply();
  return Math.max(values[0][0], values[0][1]);
}

const minOperationsToFlip = solve;
class Solution {
  minOperationsToFlip(expression) { return solve(expression); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperationsToFlip };
