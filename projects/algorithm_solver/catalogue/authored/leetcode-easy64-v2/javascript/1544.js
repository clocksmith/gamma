'use strict';

// 1544. Make The String Great (Easy).
// Specification: https://leetcode.com/problems/make-the-string-great/description/
// O(n) time, O(n) space; input contains only upper/lowercase ASCII letters.
function solve(s) {
  const stack = [];
  for (const character of s) {
    if (stack.length > 0 && Math.abs(stack[stack.length - 1].charCodeAt(0) - character.charCodeAt(0)) === 32) {
      stack.pop();
    } else {
      stack.push(character);
    }
  }
  return stack.join('');
}

const makeGood = solve;
class Solution {
  makeGood(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, makeGood };
