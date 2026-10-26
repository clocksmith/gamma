'use strict';

// 1021. Remove Outermost Parentheses (Easy).
// Specification: https://leetcode.com/problems/remove-outermost-parentheses/description/
// O(n) time and space; omit the opening and closing parentheses at primitive depth zero.
function solve(s) {
  let depth = 0;
  const result = [];
  for (const character of s) {
    if (character === '(') {
      if (depth > 0) result.push(character);
      depth++;
    } else {
      depth--;
      if (depth > 0) result.push(character);
    }
  }
  return result.join('');
}

const removeOuterParentheses = solve;
class Solution {
  removeOuterParentheses(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeOuterParentheses };
