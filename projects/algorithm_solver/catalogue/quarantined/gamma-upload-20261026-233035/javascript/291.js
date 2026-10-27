'use strict';
// 291. Word Pattern II.
function solve(pattern, s) {
  const mapping = new Map(); const used = new Set();
  function visit(patternIndex, textIndex) {
    if (patternIndex === pattern.length) return textIndex === s.length;
    const char = pattern[patternIndex];
    if (mapping.has(char)) {
      const word = mapping.get(char);
      return s.startsWith(word, textIndex) && visit(patternIndex + 1, textIndex + word.length);
    }
    const remaining = pattern.length - patternIndex - 1;
    for (let end = textIndex + 1; end <= s.length - remaining; end += 1) {
      const word = s.slice(textIndex, end);
      if (used.has(word)) continue;
      mapping.set(char, word); used.add(word);
      if (visit(patternIndex + 1, end)) return true;
      mapping.delete(char); used.delete(word);
    }
    return false;
  }
  return visit(0, 0);
}
const wordPatternMatch = solve;
class Solution { wordPatternMatch(pattern, s) { return solve(pattern, s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, wordPatternMatch };
