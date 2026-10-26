'use strict';

// 2559. Count Vowel Strings in Ranges: answer range counts from prefix totals of words with vowel endpoints.
// O(n + q) time and O(n + q) auxiliary space; inputs are read-only.
function solve(words, queries) {
  const vowels = new Set('aeiou');
  const prefix = new Int32Array(words.length + 1);
  for (let index = 0; index < words.length; index += 1) {
    const word = words[index];
    prefix[index + 1] = prefix[index]
      + Number(vowels.has(word[0]) && vowels.has(word[word.length - 1]));
  }
  return queries.map(([left, right]) => prefix[right + 1] - prefix[left]);
}

const vowelStrings = solve;
class Solution {
  vowelStrings(words, queries) { return solve(words, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, vowelStrings };
