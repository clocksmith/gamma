'use strict';

// 3983. Subsequence After One Replacement.
// Specification: https://leetcode.com/problems/subsequence-after-one-replacement/description/
// O(len(t)) time and O(1) space; match s as a subsequence of t, with at most one replacement in s. Inputs are preserved.
function solve(s, t) {
  if (s.length > t.length) return false;
  let exact = 0;
  let tolerant = 0;
  for (const character of t) {
    const previousExact = exact;
    if (exact < s.length && s[exact] === character) exact++;
    const matched = tolerant + (tolerant < s.length && s[tolerant] === character ? 1 : 0);
    tolerant = Math.min(s.length, Math.max(matched, previousExact + 1));
    if (tolerant === s.length) return true;
  }
  return false;
}

if (typeof module !== 'undefined') module.exports = { solve };
