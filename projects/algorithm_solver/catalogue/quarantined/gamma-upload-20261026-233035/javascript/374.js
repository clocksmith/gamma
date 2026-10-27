'use strict';
// 374. Guess Number Higher or Lower.
function solve(n, guessFn = globalThis.guess) {
  let left = 1; let right = n;
  while (left <= right) {
    const middle = Math.floor((left + right) / 2); const result = guessFn(middle);
    if (result === 0) return middle;
    if (result < 0) right = middle - 1; else left = middle + 1;
  }
  return -1;
}
class Solution { guessNumber(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution };
