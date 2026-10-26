'use strict';

// 2140. Solving Questions With Brainpower: choose between skipping a question and jumping past its forced break.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(questions) {
  const size = questions.length;
  const best = new Array(size + 1).fill(0);
  for (let index = size - 1; index >= 0; index -= 1) {
    const [points, skip] = questions[index];
    const following = Math.min(size, index + skip + 1);
    best[index] = Math.max(best[index + 1], points + best[following]);
  }
  return best[0];
}

const mostPoints = solve;
class Solution {
  mostPoints(questions) { return solve(questions); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mostPoints };
