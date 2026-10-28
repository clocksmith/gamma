'use strict';
// 792. Separate functional variant: process only words waiting for each letter.
function solve(s, words) {
  const waiting = Array.from({ length: 26 }, () => []);
  const counts = new Map();
  for (const word of words) counts.set(word, (counts.get(word) || 0) + 1);
  for (const [word, multiplicity] of counts) waiting[word.charCodeAt(0) - 97].push([word, 1, multiplicity]);
  let answer = 0;
  for (const char of s) {
    const index = char.charCodeAt(0) - 97;
    const ready = waiting[index];
    waiting[index] = [];
    for (const [word, position, multiplicity] of ready) {
      if (position === word.length) answer += multiplicity;
      else waiting[word.charCodeAt(position) - 97].push([word, position + 1, multiplicity]);
    }
  }
  return answer;
}
const numMatchingSubseq = solve;
class Solution { numMatchingSubseq(s, words) { return solve(s, words); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numMatchingSubseq };
