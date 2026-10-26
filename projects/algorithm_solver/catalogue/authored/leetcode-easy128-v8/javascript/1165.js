'use strict';

// 1165. Single-Row Keyboard (Easy).
// Specification: https://leetcode.com/problems/single-row-keyboard/description/
// O(word length + 26) time, O(26) space; start the finger at keyboard index zero.
function solve(keyboard, word) {
  const positions = new Array(26);
  for (let index = 0; index < keyboard.length; index++) positions[keyboard.charCodeAt(index) - 97] = index;
  let previous = 0;
  let total = 0;
  for (const character of word) {
    const current = positions[character.charCodeAt(0) - 97];
    total += Math.abs(current - previous);
    previous = current;
  }
  return total;
}

const calculateTime = solve;
class Solution {
  calculateTime(keyboard, word) { return solve(keyboard, word); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, calculateTime };
