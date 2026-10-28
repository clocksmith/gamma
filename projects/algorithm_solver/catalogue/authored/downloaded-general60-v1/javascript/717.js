'use strict';

// 717. 1-bit and 2-bit Characters (Easy).
// Specification: https://leetcode.com/problems/1-bit-and-2-bit-characters/description/
function solve(bits) {
  let i = 0;
  while (i < bits.length - 1) { i += bits[i] === 1 ? 2 : 1; }
  return i === bits.length - 1;
}
const isOneBitCharacter = solve;
class Solution { isOneBitCharacter(bits) { return solve(bits); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isOneBitCharacter };
