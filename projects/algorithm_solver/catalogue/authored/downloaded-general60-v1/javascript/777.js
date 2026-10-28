'use strict';

// 777. Swap Adjacent in LR String (Medium).
// Specification: https://leetcode.com/problems/swap-adjacent-in-lr-string/description/
function solve(start, end) {
  if (start.length !== end.length) return false;
  let i = 0; let j = 0;
  while (i < start.length && j < end.length) {
    while (i < start.length && start[i] === 'X') i++;
    while (j < end.length && end[j] === 'X') j++;
    if (i === start.length && j === end.length) return true;
    if (i === start.length || j === end.length) return false;
    if (start[i] !== end[j]) return false;
    if (start[i] === 'L' && i < j) return false;
    if (start[i] === 'R' && i > j) return false;
    i++; j++;
  }
  while (i < start.length && start[i] === 'X') i++;
  while (j < end.length && end[j] === 'X') j++;
  return i === start.length && j === end.length;
}
const canTransform = solve;
class Solution { canTransform(start, end) { return solve(start, end); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canTransform };
