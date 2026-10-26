'use strict';

// 2063. Vowels of All Substrings: count how many substrings include each vowel position.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(word) {
  let answer = 0;
  for (let index = 0; index < word.length; index += 1) {
    if ('aeiou'.includes(word[index])) answer += (index + 1) * (word.length - index);
  }
  return answer;
}

const countVowels = solve;
class Solution {
  countVowels(word) { return solve(word); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countVowels };
