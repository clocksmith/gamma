'use strict';

// 2135. Count Words Obtained After Adding a Letter: remove one distinct letter from each target mask.
// O(total characters) expected time and O(number of start words) auxiliary space; inputs are read-only.
function solve(startWords, targetWords) {
  function mask(word) {
    let bits = 0;
    for (let index = 0; index < word.length; index += 1) {
      bits |= 1 << (word.charCodeAt(index) - 97);
    }
    return bits;
  }

  const starts = new Set(startWords.map(mask));
  let answer = 0;
  for (const word of targetWords) {
    const bits = mask(word);
    for (let index = 0; index < word.length; index += 1) {
      const withoutLetter = bits ^ (1 << (word.charCodeAt(index) - 97));
      if (starts.has(withoutLetter)) {
        answer += 1;
        break;
      }
    }
  }
  return answer;
}

const wordCount = solve;
class Solution {
  wordCount(startWords, targetWords) { return solve(startWords, targetWords); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, wordCount };
