'use strict';

// 2042. Check if Numbers Are Ascending in a Sentence (Easy).
// Specification: https://leetcode.com/problems/check-if-numbers-are-ascending-in-a-sentence/description/
// O(n) time and token space; compare only numeric tokens in the stated sentence domain.
function solve(s) {
  let previous = -1;
  for (const token of s.split(' ')) {
    if (token[0] < '0' || token[0] > '9') continue;
    const value = Number(token);
    if (value <= previous) return false;
    previous = value;
  }
  return true;
}

const areNumbersAscending = solve;
class Solution {
  areNumbersAscending(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, areNumbersAscending };
