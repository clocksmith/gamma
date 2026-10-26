'use strict';

// 282. Expression Add Operators: backtracking with the last multiplicative term.
// O(n * 4^n) time; O(n^2) stack strings plus output. Inputs are preserved.
function solve(num, target) {
  // The problem's at-most-ten decimal digits keep these integer operations exact.
  const answers = [];
  function visit(start, total, last, expression) {
    if (start === num.length) {
      if (total === target) answers.push(expression);
      return;
    }
    let value = 0;
    for (let end = start; end < num.length; end += 1) {
      if (end > start && num[start] === '0') break;
      value = value * 10 + num.charCodeAt(end) - 48;
      const token = num.slice(start, end + 1);
      if (start === 0) {
        visit(end + 1, value, value, token);
      } else {
        visit(end + 1, total + value, value, expression + '+' + token);
        visit(end + 1, total - value, -value, expression + '-' + token);
        const product = last * value;
        visit(end + 1, total - last + product, product, expression + '*' + token);
      }
    }
  }
  visit(0, 0, 0, '');
  return answers;
}

const addOperators = solve;
class Solution {
  addOperators(num, target) { return solve(num, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, addOperators };
