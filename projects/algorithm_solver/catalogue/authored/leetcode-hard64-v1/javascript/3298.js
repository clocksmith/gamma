'use strict';

// 3298. Count Substrings That Can Be Rearranged to Contain a String II: multiplicity-aware sliding window.
// O(n + m) time and O(26) auxiliary space. Inputs are preserved.
function solve(word1, word2) {
  const needed = new Int32Array(26);
  for (let index = 0; index < word2.length; index += 1) needed[word2.charCodeAt(index) - 97] += 1;
  let missing = word2.length;
  let left = 0;
  let answer = 0;
  for (let right = 0; right < word1.length; right += 1) {
    let letter = word1.charCodeAt(right) - 97;
    if (needed[letter] > 0) missing -= 1;
    needed[letter] -= 1;
    while (missing === 0) {
      letter = word1.charCodeAt(left) - 97;
      needed[letter] += 1;
      if (needed[letter] > 0) missing += 1;
      left += 1;
    }
    answer += left;
  }
  return answer;
}

const validSubstringCount = solve;
class Solution {
  validSubstringCount(word1, word2) { return solve(word1, word2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, validSubstringCount };
