'use strict';

// 2947. Count Beautiful Substrings I: enumerate substrings while accumulating vowel and consonant counts.
// O(n * n) time and O(1) auxiliary space; inputs are read-only.
function solve(s, k) {
  const vowels = new Set('aeiou');
  let total = 0;
  for (let left = 0; left < s.length; left += 1) {
    let vowelCount = 0;
    let consonantCount = 0;
    for (let right = left; right < s.length; right += 1) {
      if (vowels.has(s[right])) vowelCount += 1;
      else consonantCount += 1;
      if (vowelCount === consonantCount && vowelCount * consonantCount % k === 0) total += 1;
    }
  }
  return total;
}

const beautifulSubstrings = solve;
class Solution {
  beautifulSubstrings(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, beautifulSubstrings };
