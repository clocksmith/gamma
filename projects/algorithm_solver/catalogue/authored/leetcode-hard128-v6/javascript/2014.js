'use strict';

// 2014. Longest Subsequence Repeated k Times.
// Breadth-first extension of repeatable candidates, bounded by per-letter quotas. O(n*A*C) time, O(C*L) space for C candidates of length at most L.

function solve(s, k) {
  const counts = new Map();
  for (const char of s) counts.set(char, (counts.get(char) || 0) + 1);
  const alphabet = [...counts.keys()].filter(char => counts.get(char) >= k).sort();
  function repeats(candidate) {
    let position = 0, complete = 0;
    for (const char of s) {
      if (char === candidate[position]) {
        position += 1;
        if (position === candidate.length) { complete += 1; if (complete === k) return true; position = 0; }
      }
    }
    return false;
  }
  let level = [''], answer = '';
  while (level.length > 0) {
    const following = [];
    for (const prefix of level) {
      for (const char of alphabet) {
        let used = 0;
        for (const value of prefix) if (value === char) used += 1;
        if (used >= Math.floor(counts.get(char) / k)) continue;
        const candidate = prefix + char;
        if (repeats(candidate)) { following.push(candidate); answer = candidate; }
      }
    }
    level = following;
  }
  return answer;
}

const longestSubsequenceRepeatedK = solve;
class Solution {
  longestSubsequenceRepeatedK(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestSubsequenceRepeatedK };
