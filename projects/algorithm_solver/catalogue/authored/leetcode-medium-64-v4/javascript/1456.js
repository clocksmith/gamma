'use strict';

// 1456. Maximum Number of Vowels in a Substring of Given Length: update the vowel count as a fixed-length window moves.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s, k) {
  const vowels = new Set('aeiou');
  let count = 0;
  let best = 0;
  for (let index = 0; index < s.length; index += 1) {
    if (vowels.has(s[index])) count += 1;
    if (index >= k && vowels.has(s[index - k])) count -= 1;
    if (index + 1 >= k) best = Math.max(best, count);
  }
  return best;
}

const maxVowels = solve;
class Solution {
  maxVowels(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxVowels };
