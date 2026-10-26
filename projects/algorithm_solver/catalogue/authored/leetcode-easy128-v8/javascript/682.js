'use strict';

// 682. Baseball Game (Easy).
// Specification: https://leetcode.com/problems/baseball-game/description/
// O(n) time and space; maintain the valid score stack under the valid-operation contract.
function solve(operations) {
  const scores = [];
  for (const operation of operations) {
    if (operation === 'C') scores.pop();
    else if (operation === 'D') scores.push(2 * scores[scores.length - 1]);
    else if (operation === '+') scores.push(scores[scores.length - 1] + scores[scores.length - 2]);
    else scores.push(Number(operation));
  }
  let total = 0;
  for (const score of scores) total += score;
  return total;
}

const calPoints = solve;
class Solution {
  calPoints(operations) { return solve(operations); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, calPoints };
