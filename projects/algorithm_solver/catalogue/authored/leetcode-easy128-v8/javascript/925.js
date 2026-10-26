'use strict';

// 925. Long Pressed Name (Easy).
// Specification: https://leetcode.com/problems/long-pressed-name/description/
// O(n + m) time, O(1) space; unmatched typed letters must repeat the immediately previous letter.
function solve(name, typed) {
  let matched = 0;
  for (let index = 0; index < typed.length; index++) {
    if (matched < name.length && typed[index] === name[matched]) matched++;
    else if (index === 0 || typed[index] !== typed[index - 1]) return false;
  }
  return matched === name.length;
}

const isLongPressedName = solve;
class Solution {
  isLongPressedName(name, typed) { return solve(name, typed); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isLongPressedName };
