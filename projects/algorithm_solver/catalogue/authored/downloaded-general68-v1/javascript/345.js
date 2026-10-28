'use strict';

// 345. Reverse Vowels of a String (Easy).
// Specification: https://leetcode.com/problems/reverse-vowels-of-a-string/description/
const VOWELS = new Set(['a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U']);
function solve(s) {
  const chars = [...s];
  let left = 0; let right = chars.length - 1;
  while (left < right) {
    while (left < right && !VOWELS.has(chars[left])) left++;
    while (left < right && !VOWELS.has(chars[right])) right--;
    if (left < right) { const tmp = chars[left]; chars[left] = chars[right]; chars[right] = tmp; left++; right--; }
  }
  return chars.join('');
}
const reverseVowels = solve;
class Solution { reverseVowels(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseVowels };
