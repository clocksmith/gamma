'use strict';

// 1253. Reconstruct a 2-Row Binary Matrix (Medium).
// Specification: https://leetcode.com/problems/reconstruct-a-2-row-binary-matrix/description/
function solve(upper, lower, colsum) {
  const top = new Array(colsum.length).fill(0);
  const bottom = new Array(colsum.length).fill(0);
  for (let i = 0; i < colsum.length; i++) {
    if (colsum[i] === 2) {
      if (upper === 0 || lower === 0) return [];
      top[i] = 1; bottom[i] = 1; upper--; lower--;
    }
  }
  for (let i = 0; i < colsum.length; i++) {
    if (colsum[i] === 1) {
      if (upper > 0) { top[i] = 1; upper--; }
      else if (lower > 0) { bottom[i] = 1; lower--; }
      else return [];
    }
  }
  if (upper !== 0 || lower !== 0) return [];
  return [top, bottom];
}
const reconstructMatrix = solve;
class Solution { reconstructMatrix(upper, lower, colsum) { return solve(upper, lower, colsum); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reconstructMatrix };
