'use strict';

// 3305. Count of Substrings Containing Every Vowel and K Consonants I (Medium).
// Specification: https://leetcode.com/problems/count-of-substrings-containing-every-vowel-and-k-consonants-i/description/
function solve(word, k) {
  const vowels = new Set(['a', 'e', 'i', 'o', 'u']);
  let ans = 0;
  for (let i = 0; i < word.length; i++) {
    const seen = new Set(); let cons = 0;
    for (let j = i; j < word.length; j++) {
      if (vowels.has(word[j])) seen.add(word[j]); else cons++;
      if (seen.size === 5 && cons === k) ans++;
      if (cons > k) break;
    }
  }
  return ans;
}
const countOfSubstrings = solve;
class Solution { countOfSubstrings(word, k) { return solve(word, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, countOfSubstrings };
