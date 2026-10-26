'use strict';

// 3035. Maximum Palindromes After Operations: spend globally available equal-character pairs on the shortest words first.
// O(S + n log n) time and O(n) auxiliary space, where S is the total character count; inputs are read-only.
function solve(words) {
  const counts = new Int32Array(26);
  for (const word of words) {
    for (const character of word) counts[character.charCodeAt(0) - 97] += 1;
  }
  let pairs = 0;
  for (const count of counts) pairs += Math.floor(count / 2);
  const lengths = words.map(word => word.length).sort((left, right) => left - right);
  let completed = 0;
  for (const length of lengths) {
    const needed = Math.floor(length / 2);
    if (needed > pairs) break;
    pairs -= needed;
    completed += 1;
  }
  return completed;
}

const maxPalindromesAfterOperations = solve;
class Solution {
  maxPalindromesAfterOperations(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxPalindromesAfterOperations };
