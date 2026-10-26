'use strict';

// 1047. Remove All Adjacent Duplicates In String (Easy).
// Specification: https://leetcode.com/problems/remove-all-adjacent-duplicates-in-string/description/
// O(n) time and space; cancelling neighboring equal characters maintains the reduced prefix.
function solve(s) {
  const stack = [];
  for (const character of s) {
    if (stack.length > 0 && stack[stack.length - 1] === character) stack.pop();
    else stack.push(character);
  }
  return stack.join('');
}

const removeDuplicates = solve;
class Solution {
  removeDuplicates(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeDuplicates };
