'use strict';

// 2047. Number of Valid Words in a Sentence (Easy).
// Specification: https://leetcode.com/problems/number-of-valid-words-in-a-sentence/description/
// O(n) time and O(n) token storage; apply the lowercase ASCII token rules.
function solve(sentence) {
  let result = 0;
  for (const token of sentence.split(' ')) {
    if (token.length === 0) continue;
    let valid = true;
    let hyphens = 0;
    for (let index = 0; index < token.length; index++) {
      const character = token[index];
      if (character >= '0' && character <= '9') {
        valid = false;
        break;
      }
      if (character === '-') {
        hyphens++;
        if (hyphens > 1 || index === 0 || index + 1 === token.length
            || token[index - 1] < 'a' || token[index - 1] > 'z'
            || token[index + 1] < 'a' || token[index + 1] > 'z') {
          valid = false;
          break;
        }
      } else if (character === '!' || character === '.' || character === ',') {
        if (index + 1 !== token.length) {
          valid = false;
          break;
        }
      }
    }
    if (valid) result++;
  }
  return result;
}

const countValidWords = solve;
class Solution {
  countValidWords(sentence) { return solve(sentence); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countValidWords };
