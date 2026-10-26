'use strict';

// 3723. Maximize Sum of Squares of Digits.
// O(num) time and output space; concentrating the digit sum maximizes the convex square objective.
function solve(num, sum) {
  if (sum > 9 * num) return '';
  const answer = [];
  let remaining = sum;
  for (let index = 0; index < num; index += 1) {
    const digit = Math.min(9, remaining);
    answer.push(String(digit));
    remaining -= digit;
  }
  return answer.join('');
}

const maxSumOfSquares = solve;
class Solution {
  maxSumOfSquares(num, sum) { return solve(num, sum); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSumOfSquares };
