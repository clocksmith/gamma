'use strict';

// 1796. Second Largest Digit in a String (Easy).
// Specification: https://leetcode.com/problems/second-largest-digit-in-a-string/description/
// O(n) time, O(1) space; track the two greatest distinct ASCII digits.
function solve(s) {
  let largest = -1;
  let secondLargest = -1;
  for (const character of s) {
    if (character < '0' || character > '9') continue;
    const digit = character.charCodeAt(0) - 48;
    if (digit > largest) {
      secondLargest = largest;
      largest = digit;
    } else if (digit < largest && digit > secondLargest) {
      secondLargest = digit;
    }
  }
  return secondLargest;
}

const secondHighest = solve;
class Solution {
  secondHighest(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, secondHighest };
