'use strict';

// 20. Valid Parentheses (Easy).
// Specification: https://leetcode.com/problems/valid-parentheses/description/
// O(n) time and space; match closing brackets against the latest unmatched opening.
function solve(s) {
  const opening = { ')': '(', ']': '[', '}': '{' };
  const stack = [];
  for (const character of s) {
    if (character === '(' || character === '[' || character === '{') {
      stack.push(character);
    } else if (stack.pop() !== opening[character]) {
      return false;
    }
  }
  return stack.length === 0;
}

const isValid = solve;
class Solution {
  isValid(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isValid };
