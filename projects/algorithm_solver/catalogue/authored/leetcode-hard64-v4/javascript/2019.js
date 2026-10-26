'use strict';

// 2019. The Score of Students Solving Math Expression. Precedence evaluation plus bounded parenthesization DP; O(m^3*U^2+A) time, O(m^2*U) space, U=1002. Inputs are preserved.

function solve(s, answers) {
  const digits = [];
  const operators = [];
  for (let index = 0; index < s.length; index += 1) {
    if (index % 2 === 0) digits.push(Number(s[index]));
    else operators.push(s[index]);
  }
  let correct = 0;
  let product = digits[0];
  for (let index = 0; index < operators.length; index += 1) {
    if (operators[index] === '*') product *= digits[index + 1];
    else {
      correct += product;
      product = digits[index + 1];
    }
  }
  correct += product;
  const size = digits.length;
  const possible = Array.from({ length: size }, () => Array.from({ length: size }, () => new Set()));
  for (let index = 0; index < size; index += 1) possible[index][index].add(digits[index]);
  for (let width = 2; width <= size; width += 1) {
    for (let left = 0; left + width <= size; left += 1) {
      const right = left + width - 1;
      const outcomes = possible[left][right];
      for (let split = left; split < right; split += 1) {
        for (const first of possible[left][split]) {
          for (const second of possible[split + 1][right]) {
            const value = operators[split] === '+' ? first + second : first * second;
            // An overflow sentinel preserves expressions later multiplied by zero.
            outcomes.add(Math.min(value, 1001));
          }
        }
      }
    }
  }
  const alternatives = possible[0][size - 1];
  let score = 0;
  for (const value of answers) {
    if (value === correct) score += 5;
    else if (alternatives.has(value)) score += 2;
  }
  return score;
}

const scoreOfStudents = solve;
class Solution {
  scoreOfStudents(s, answers) { return solve(s, answers); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, scoreOfStudents };
