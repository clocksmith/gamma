'use strict';

// 2496. Maximum Value of a String in an Array (Easy).
// Specification: https://leetcode.com/problems/maximum-value-of-a-string-in-an-array/description/
// O(total characters) time, O(1) auxiliary space; strings contain at most nine characters.
function solve(strs) {
  let result = 0;
  for (const text of strs) {
    let value = 0;
    for (const character of text) {
      if (character < '0' || character > '9') {
        value = text.length;
        break;
      }
      value = value * 10 + character.charCodeAt(0) - 48;
    }
    result = Math.max(result, value);
  }
  return result;
}

const maximumValue = solve;
class Solution {
  maximumValue(strs) { return solve(strs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumValue };
