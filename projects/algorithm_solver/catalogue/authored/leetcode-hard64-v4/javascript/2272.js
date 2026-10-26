'use strict';

// 2272. Substring With Largest Variance. Ordered-letter Kadane scans retaining a required minority; O(A^2*n) time and O(A) space. Inputs are preserved.

function solve(s) {
  const frequency = new Map();
  for (const character of s) frequency.set(character, (frequency.get(character) || 0) + 1);
  let answer = 0;
  for (const major of frequency.keys()) {
    for (const minor of frequency.keys()) {
      if (major === minor) continue;
      let remainingMinor = frequency.get(minor);
      let difference = 0;
      let hasMinor = false;
      for (const character of s) {
        if (character === major) difference += 1;
        else if (character === minor) {
          difference -= 1;
          remainingMinor -= 1;
          hasMinor = true;
        } else {
          continue;
        }
        if (hasMinor) answer = Math.max(answer, difference);
        if (difference < 0 && remainingMinor > 0) {
          difference = 0;
          hasMinor = false;
        }
      }
    }
  }
  return answer;
}

const largestVariance = solve;
class Solution {
  largestVariance(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestVariance };
