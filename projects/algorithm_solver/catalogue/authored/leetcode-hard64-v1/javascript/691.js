'use strict';

// 691. Stickers to Spell Word: memoized remaining letter counts with first-needed-letter pruning.
// O(26 * S * C) time and O(26 * (S + C)) space; S = count states, C = stickers. Inputs are preserved.
function solve(stickers, target) {
  const needed = Array(26).fill(0);
  for (const character of target) needed[character.charCodeAt(0) - 97] += 1;
  const vectors = [];
  const seen = new Set();
  for (const sticker of stickers) {
    const counts = Array(26).fill(0);
    for (const character of sticker) {
      const index = character.charCodeAt(0) - 97;
      counts[index] = Math.min(needed[index], counts[index] + 1);
    }
    const key = counts.join(',');
    if (counts.some(count => count > 0) && !seen.has(key)) {
      seen.add(key);
      vectors.push(counts);
    }
  }
  const memo = new Map();
  function visit(remaining) {
    const pivot = remaining.findIndex(count => count > 0);
    if (pivot < 0) return 0;
    const key = remaining.join(',');
    if (memo.has(key)) return memo.get(key);
    let best = target.length + 1;
    for (const vector of vectors) {
      if (vector[pivot] === 0) continue;
      const following = remaining.map((count, index) => Math.max(0, count - vector[index]));
      const child = visit(following);
      if (child >= 0) best = Math.min(best, child + 1);
    }
    const answer = best > target.length ? -1 : best;
    memo.set(key, answer);
    return answer;
  }
  return visit(needed);
}

const minStickers = solve;
class Solution {
  minStickers(stickers, target) { return solve(stickers, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minStickers };
