'use strict';

// 408. Valid Word Abbreviation (Easy).
// Specification: https://leetcode.com/problems/valid-word-abbreviation/description/
function solve(word, abbr) {
  let i = 0; let j = 0;
  while (i < word.length && j < abbr.length) {
    if (abbr[j] >= '0' && abbr[j] <= '9') {
      if (abbr[j] === '0') return false;
      let number = 0;
      while (j < abbr.length && abbr[j] >= '0' && abbr[j] <= '9') { number = number * 10 + Number(abbr[j]); j++; }
      i += number;
    } else {
      if (word[i] !== abbr[j]) return false;
      i++; j++;
    }
  }
  return i === word.length && j === abbr.length;
}
const validWordAbbreviation = solve;
class Solution { validWordAbbreviation(word, abbr) { return solve(word, abbr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, validWordAbbreviation };
