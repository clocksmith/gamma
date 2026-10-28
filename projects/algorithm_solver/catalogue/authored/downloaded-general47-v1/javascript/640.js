'use strict';

// 640. Solve the Equation (Medium).
// Specification: https://leetcode.com/problems/solve-the-equation/description/
function parseSide(text) {
  let coefficient = 0; let constant = 0;
  let sign = 1; let i = 0;
  while (i < text.length) {
    if (text[i] === '+') { sign = 1; i++; continue; }
    if (text[i] === '-') { sign = -1; i++; continue; }
    let numberText = '';
    while (i < text.length && text[i] >= '0' && text[i] <= '9') { numberText += text[i]; i++; }
    if (i < text.length && text[i] === 'x') {
      coefficient += sign * (numberText === '' ? 1 : Number(numberText));
      i++;
    } else {
      constant += sign * Number(numberText);
    }
  }
  return [coefficient, constant];
}
function solve(equation) {
  const parts = equation.split('=');
  const left = parseSide(parts[0]);
  const right = parseSide(parts[1]);
  const coefficient = left[0] - right[0];
  const constant = right[1] - left[1];
  if (coefficient === 0) return constant === 0 ? 'Infinite solutions' : 'No solution';
  return 'x=' + String(Math.trunc(constant / coefficient));
}
const solveEquation = solve;
class Solution { solveEquation(equation) { return solve(equation); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, solveEquation };
