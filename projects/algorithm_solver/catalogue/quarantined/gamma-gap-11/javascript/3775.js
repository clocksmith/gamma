'use strict';

// 3775. Reverse Words With Same Vowel Count.
// O(n) time and O(n) space; preserve the first word and single-space separators.
function solve(s) {
  const words = s.split(' ');
  const vowels = new Set('aeiou');
  function count(word) {
    let total = 0;
    for (const char of word) if (vowels.has(char)) total += 1;
    return total;
  }
  const target = count(words[0]);
  for (let index = 1; index < words.length; index += 1) {
    if (count(words[index]) === target) words[index] = words[index].split('').reverse().join('');
  }
  return words.join(' ');
}

const reverseWords = solve;
class Solution {
  reverseWords(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseWords };
