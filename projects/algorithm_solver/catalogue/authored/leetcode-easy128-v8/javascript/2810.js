'use strict';

// 2810. Faulty Keyboard (Easy).
// Specification: https://leetcode.com/problems/faulty-keyboard/description/
// O(n) time and space; toggle orientation and postpone reversal until final assembly.
function solve(s) {
  const left = [];
  const right = [];
  let reversed = false;
  for (const character of s) {
    if (character === 'i') reversed = !reversed;
    else if (reversed) left.push(character);
    else right.push(character);
  }
  const result = left.reverse().concat(right);
  if (reversed) result.reverse();
  return result.join('');
}

const finalString = solve;
class Solution {
  finalString(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, finalString };
