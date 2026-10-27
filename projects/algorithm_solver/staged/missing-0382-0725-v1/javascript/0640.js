'use strict';

// 640. Solve the Equation.

function solve(equation) {
  function parse(text) {
    let coefficient = 0, constant = 0;
    for (const term of text.match(/[+-]?[^+-]+/g) || []) {
      if (term.endsWith('x')) {
        const factor = term.slice(0, -1);
        coefficient += factor === '-' ? -1 : (factor === '' || factor === '+') ? 1 : Number(factor);
      } else constant += Number(term);
    }
    return [coefficient, constant];
  }
  const [left, right] = equation.split('='), [a, b] = parse(left), [c, d] = parse(right);
  const coefficient = a - c, value = d - b;
  if (coefficient === 0) return value === 0 ? 'Infinite solutions' : 'No solution';
  return 'x=' + String(value / coefficient);
}

const solveEquation = solve;
class Solution {
  solveEquation(equation) { return solve(equation); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, solveEquation };
