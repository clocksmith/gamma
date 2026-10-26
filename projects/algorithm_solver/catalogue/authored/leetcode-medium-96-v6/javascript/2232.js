'use strict';

// 2232. Minimize Result by Adding Parentheses to Expression: enumerate legal parenthesis boundaries and evaluate the resulting factors.
// O(L^3) time and O(L) auxiliary space for expression length L; inputs are read-only.
function solve(expression) {
  const [left, right] = expression.split('+');
  let best = Infinity;
  let answer = '';
  for (let start = 0; start < left.length; start += 1) {
    const outerLeft = start ? Number(left.slice(0, start)) : 1;
    const innerLeft = Number(left.slice(start));
    for (let end = 1; end <= right.length; end += 1) {
      const innerRight = Number(right.slice(0, end));
      const outerRight = end < right.length ? Number(right.slice(end)) : 1;
      const value = outerLeft * (innerLeft + innerRight) * outerRight;
      if (value < best) {
        best = value;
        answer = left.slice(0, start) + '(' + left.slice(start) + '+' + right.slice(0, end) + ')' + right.slice(end);
      }
    }
  }
  return answer;
}

const minimizeResult = solve;
class Solution {
  minimizeResult(expression) { return solve(expression); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimizeResult };
