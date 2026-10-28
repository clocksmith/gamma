'use strict';

// 1255. Maximum Score Words Formed by Letters (Hard).
// Specification: https://leetcode.com/problems/maximum-score-words-formed-by-letters/description/
function solve(words, letters, score) {
  const available = new Array(26).fill(0);
  for (const ch of letters) available[ch.charCodeAt(0) - 97]++;
  let best = 0;
  function backtrack(index, currentScore) {
    best = Math.max(best, currentScore);
    for (let i = index; i < words.length; i++) {
      const needed = new Array(26).fill(0);
      let wordScore = 0; let ok = true;
      for (const ch of words[i]) { const code = ch.charCodeAt(0) - 97; needed[code]++; wordScore += score[code]; }
      for (let letter = 0; letter < 26; letter++) { if (needed[letter] > available[letter]) { ok = false; break; } }
      if (!ok) continue;
      for (let letter = 0; letter < 26; letter++) available[letter] -= needed[letter];
      backtrack(i + 1, currentScore + wordScore);
      for (let letter = 0; letter < 26; letter++) available[letter] += needed[letter];
    }
  }
  backtrack(0, 0);
  return best;
}
const maxScoreWords = solve;
class Solution { maxScoreWords(words, letters, score) { return solve(words, letters, score); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxScoreWords };
