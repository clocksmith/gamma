'use strict';

// 1427. Perform String Shifts (Easy).
// Specification: https://leetcode.com/problems/perform-string-shifts/description/
function solve(s, shift) {
  if (s.length === 0) return s;
  let net = 0;
  for (const [direction, amount] of shift) net += direction === 1 ? amount : -amount;
  net = ((net % s.length) + s.length) % s.length;
  if (net === 0) return s;
  return s.slice(-net) + s.slice(0, s.length - net);
}
const stringShift = solve;
class Solution { stringShift(...args) { return solve(...args); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, stringShift };
