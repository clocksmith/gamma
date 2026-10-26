'use strict';

// 2697. Lexicographically Smallest Palindrome (Easy).
// Specification: https://leetcode.com/problems/lexicographically-smallest-palindrome/description/
// O(n) time and space; choose the smaller letter in each mirrored pair.
function solve(s) {
  const characters = s.split('');
  for (let left = 0, right = characters.length - 1; left < right; left++, right--) {
    const smaller = characters[left] < characters[right] ? characters[left] : characters[right];
    characters[left] = smaller;
    characters[right] = smaller;
  }
  return characters.join('');
}

const makeSmallestPalindrome = solve;
class Solution {
  makeSmallestPalindrome(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, makeSmallestPalindrome };
