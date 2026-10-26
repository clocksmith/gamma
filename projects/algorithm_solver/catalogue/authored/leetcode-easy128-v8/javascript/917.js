'use strict';

// 917. Reverse Only Letters (Easy).
// Specification: https://leetcode.com/problems/reverse-only-letters/description/
// O(n) time and space; exchange ASCII letters while leaving nonletters at their indices.
function solve(s) {
  const result = s.split('');
  function isLetter(character) {
    return (character >= 'a' && character <= 'z') || (character >= 'A' && character <= 'Z');
  }
  let left = 0;
  let right = result.length - 1;
  while (left < right) {
    if (!isLetter(result[left])) left++;
    else if (!isLetter(result[right])) right--;
    else {
      [result[left], result[right]] = [result[right], result[left]];
      left++;
      right--;
    }
  }
  return result.join('');
}

const reverseOnlyLetters = solve;
class Solution {
  reverseOnlyLetters(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseOnlyLetters };
