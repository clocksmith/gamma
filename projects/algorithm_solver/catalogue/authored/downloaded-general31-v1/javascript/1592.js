'use strict';

// 1592. Rearrange Spaces Between Words (Easy).
// Specification: https://leetcode.com/problems/rearrange-spaces-between-words/description/
function solve(text) {
  const words = text.split(' ').filter((w) => w.length > 0);
  let spaces = 0;
  for (const ch of text) { if (ch === ' ') spaces++; }
  if (words.length === 1) return words[0] + ' '.repeat(spaces);
  const between = Math.floor(spaces / (words.length - 1));
  const trailing = spaces % (words.length - 1);
  return words.join(' '.repeat(between)) + ' '.repeat(trailing);
}
const reorderSpaces = solve;
class Solution { reorderSpaces(text) { return solve(text); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reorderSpaces };
