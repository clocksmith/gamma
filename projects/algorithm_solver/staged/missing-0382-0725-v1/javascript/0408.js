'use strict';

// 408. Valid Word Abbreviation.

function solve(word, abbr) {
  let i = 0, j = 0;
  while (j < abbr.length) {
    if (abbr[j] >= '0' && abbr[j] <= '9') {
      if (abbr[j] === '0') return false;
      let count = 0;
      while (j < abbr.length && abbr[j] >= '0' && abbr[j] <= '9') {
        count = count * 10 + Number(abbr[j]); j += 1;
      }
      i += count;
      if (i > word.length) return false;
    } else {
      if (i >= word.length || word[i] !== abbr[j]) return false;
      i += 1; j += 1;
    }
  }
  return i === word.length;
}

const validWordAbbreviation = solve;
class Solution {
  validWordAbbreviation(word, abbr) { return solve(word, abbr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, validWordAbbreviation };
