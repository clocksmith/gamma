'use strict';

// 2982. Find Longest Special Substring That Occurs Thrice II: retain each character's three longest runs and account for overlapping occurrences.
// O(n) time and O(1) auxiliary space for the lowercase alphabet; inputs are read-only.
function solve(s) {
  const longest = Array.from({ length: 26 }, () => [0, 0, 0]);
  let left = 0;
  while (left < s.length) {
    let right = left + 1;
    while (right < s.length && s[right] === s[left]) right += 1;
    const runs = longest[s.charCodeAt(left) - 97];
    const length = right - left;
    if (length >= runs[0]) {
      runs[2] = runs[1];
      runs[1] = runs[0];
      runs[0] = length;
    } else if (length >= runs[1]) {
      runs[2] = runs[1];
      runs[1] = length;
    } else if (length > runs[2]) runs[2] = length;
    left = right;
  }
  let best = 0;
  for (const [first, second, third] of longest) {
    best = Math.max(best, first - 2, Math.min(first - 1, second), third);
  }
  return best > 0 ? best : -1;
}

const maximumLength = solve;
class Solution {
  maximumLength(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumLength };
