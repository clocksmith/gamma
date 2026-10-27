'use strict';

// 424. Longest Repeating Character Replacement. Sliding window with a nondecreasing maximum frequency bound.

function solve(s, k) {
  const counts = new Map();
  let left = 0, maximum = 0, answer = 0;
  for (let right = 0; right < s.length; right += 1) {
    counts.set(s[right], (counts.get(s[right]) || 0) + 1);
    maximum = Math.max(maximum, counts.get(s[right]));
    while (right - left + 1 - maximum > k) {
      counts.set(s[left], counts.get(s[left]) - 1); left += 1;
    }
    answer = Math.max(answer, right - left + 1);
  }
  return answer;
}

const characterReplacement = solve;
class Solution {
  characterReplacement(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, characterReplacement };
