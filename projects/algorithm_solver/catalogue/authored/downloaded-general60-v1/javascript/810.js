'use strict';

// 810. Chalkboard XOR Game (Hard).
// Specification: https://leetcode.com/problems/chalkboard-xor-game/description/
function solve(nums) {
  let xor = 0;
  for (const value of nums) xor ^= value;
  return xor === 0 || nums.length % 2 === 0;
}
const xorGame = solve;
class Solution { xorGame(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, xorGame };
