'use strict';

// 1414. Find the Minimum Number of Fibonacci Numbers Whose Sum Is K: subtract the largest usable Fibonacci number at each step.
// O(log(k + 1)) time and O(log(k + 1)) auxiliary space; inputs are read-only.
function solve(k) {
  const fibonacci = [1, 2];
  while (fibonacci[fibonacci.length - 1] < k) {
    fibonacci.push(fibonacci[fibonacci.length - 1] + fibonacci[fibonacci.length - 2]);
  }
  let remaining = k;
  let count = 0;
  for (let index = fibonacci.length - 1; index >= 0; index -= 1) {
    if (fibonacci[index] <= remaining) {
      remaining -= fibonacci[index];
      count += 1;
    }
  }
  return count;
}

const findMinFibonacciNumbers = solve;
class Solution {
  findMinFibonacciNumbers(k) { return solve(k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMinFibonacciNumbers };
