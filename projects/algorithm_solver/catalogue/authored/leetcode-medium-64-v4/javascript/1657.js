'use strict';

// 1657. Determine if Two Strings Are Close: require the same letter support and the same multiset of frequencies.
// O(n + m) time and O(1) auxiliary space for the fixed lowercase alphabet; inputs are read-only.
function solve(word1, word2) {
  if (word1.length !== word2.length) return false;
  const first = new Array(26).fill(0);
  const second = new Array(26).fill(0);
  for (const letter of word1) first[letter.charCodeAt(0) - 97] += 1;
  for (const letter of word2) second[letter.charCodeAt(0) - 97] += 1;
  for (let index = 0; index < 26; index += 1) {
    if ((first[index] === 0) !== (second[index] === 0)) return false;
  }
  first.sort((a, b) => a - b);
  second.sort((a, b) => a - b);
  return first.every((count, index) => count === second[index]);
}

const closeStrings = solve;
class Solution {
  closeStrings(word1, word2) { return solve(word1, word2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, closeStrings };
