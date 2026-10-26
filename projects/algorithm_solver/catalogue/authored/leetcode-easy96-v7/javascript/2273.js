'use strict';

// 2273. Find Resultant Array After Removing Anagrams (Easy).
// Specification: https://leetcode.com/problems/find-resultant-array-after-removing-anagrams/description/
// O(total characters + 26n) time, O(n) result references; compare adjacent retained signatures; preserve words.
function solve(words) {
  const result = [];
  let previous = null;
  for (const word of words) {
    const counts = new Array(26).fill(0);
    for (const character of word) counts[character.charCodeAt(0) - 97]++;
    const signature = counts.join(',');
    if (signature !== previous) {
      result.push(word);
      previous = signature;
    }
  }
  return result;
}

const removeAnagrams = solve;
class Solution {
  removeAnagrams(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeAnagrams };
