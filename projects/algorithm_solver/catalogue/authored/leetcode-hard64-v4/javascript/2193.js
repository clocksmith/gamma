'use strict';

// 2193. Minimum Number of Moves to Make Palindrome. Greedy matching from both ends using adjacent swaps; O(n^2) time and O(n) space. Inputs are preserved.

function solve(s) {
  const characters = s.split('');
  let left = 0;
  let right = characters.length - 1;
  let moves = 0;
  while (left < right) {
    let match = right;
    while (characters[match] !== characters[left]) match -= 1;
    if (match === left) {
      [characters[left], characters[left + 1]] = [characters[left + 1], characters[left]];
      moves += 1;
      continue;
    }
    for (let index = match; index < right; index += 1) {
      [characters[index], characters[index + 1]] = [characters[index + 1], characters[index]];
    }
    moves += right - match;
    left += 1;
    right -= 1;
  }
  return moves;
}

const minMovesToMakePalindrome = solve;
class Solution {
  minMovesToMakePalindrome(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMovesToMakePalindrome };
