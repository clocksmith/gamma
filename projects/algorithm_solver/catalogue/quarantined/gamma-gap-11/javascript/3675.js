'use strict';

// 3675. Minimum Operations to Transform String.
// O(n) time and O(1) auxiliary space; input is preserved.
function solve(s) {
  let answer = 0;
  for (const character of s) {
    if (character !== 'a') answer = Math.max(answer, 123 - character.charCodeAt(0));
  }
  return answer;
}

const minOperations = solve;
class Solution {
  minOperations(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
