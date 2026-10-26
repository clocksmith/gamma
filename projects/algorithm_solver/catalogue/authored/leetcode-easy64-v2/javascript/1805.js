'use strict';

// 1805. Number of Different Integers in a String (Easy).
// Specification: https://leetcode.com/problems/number-of-different-integers-in-a-string/description/
// O(n) expected time, O(n) space; normalize digit strings without numeric parsing.
function solve(word) {
  const values = new Set();
  let index = 0;
  while (index < word.length) {
    if (word[index] < '0' || word[index] > '9') {
      index++;
      continue;
    }
    let start = index;
    while (index < word.length && word[index] >= '0' && word[index] <= '9') index++;
    while (start < index - 1 && word[start] === '0') start++;
    values.add(word.slice(start, index));
  }
  return values.size;
}

const numDifferentIntegers = solve;
class Solution {
  numDifferentIntegers(word) { return solve(word); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numDifferentIntegers };
