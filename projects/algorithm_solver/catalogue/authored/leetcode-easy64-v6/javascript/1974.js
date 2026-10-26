'use strict';

// 1974. Minimum Time to Type Word Using Special Typewriter (Easy).
// Specification: https://leetcode.com/problems/minimum-time-to-type-word-using-special-typewriter/description/
// O(n) time, O(1) space; choose the shorter circular movement and pay one second per letter.
function solve(word) {
  let position = 0;
  let seconds = 0;
  for (const character of word) {
    const target = character.charCodeAt(0) - 97;
    const distance = Math.abs(target - position);
    seconds += Math.min(distance, 26 - distance) + 1;
    position = target;
  }
  return seconds;
}

const minTimeToType = solve;
class Solution {
  minTimeToType(word) { return solve(word); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minTimeToType };
