'use strict';

// 844. Backspace String Compare (Easy).
// Specification: https://leetcode.com/problems/backspace-string-compare/description/
// O(n + m) time and space; build each final string with a backspace-aware stack.
function solve(s, t) {
  function render(text) {
    const stack = [];
    for (const character of text) {
      if (character === '#') stack.pop();
      else stack.push(character);
    }
    return stack.join('');
  }
  return render(s) === render(t);
}

const backspaceCompare = solve;
class Solution {
  backspaceCompare(s, t) { return solve(s, t); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, backspaceCompare };
