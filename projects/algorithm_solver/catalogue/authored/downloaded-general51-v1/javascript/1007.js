'use strict';

// 1007. Minimum Domino Rotations For Equal Row (Medium).
// Specification: https://leetcode.com/problems/minimum-domino-rotations-for-equal-row/description/
function countFor(tops, bottoms, target) {
  let rotationsTop = 0; let rotationsBottom = 0;
  for (let i = 0; i < tops.length; i++) {
    if (tops[i] !== target && bottoms[i] !== target) return Infinity;
    if (tops[i] !== target) rotationsTop++;
    if (bottoms[i] !== target) rotationsBottom++;
  }
  return Math.min(rotationsTop, rotationsBottom);
}
function solve(tops, bottoms) {
  const answer = Math.min(countFor(tops, bottoms, tops[0]), countFor(tops, bottoms, bottoms[0]));
  return answer === Infinity ? -1 : answer;
}
const minDominoRotations = solve;
class Solution { minDominoRotations(tops, bottoms) { return solve(tops, bottoms); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDominoRotations };
