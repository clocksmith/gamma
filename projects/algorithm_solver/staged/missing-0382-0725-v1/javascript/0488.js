'use strict';

// 488. Zuma Game. Memoized insertion search includes both matching insertions and splitting an equal-color pair.

function solve(board, hand) {
  const colors = 'RYBGW', initial = Array(5).fill(0), memo = new Map();
  for (const char of hand) initial[colors.indexOf(char)] += 1;
  function shrink(text) {
    while (true) {
      const pieces = [];
      let changed = false;
      for (let i = 0; i < text.length;) {
        let j = i + 1;
        while (j < text.length && text[j] === text[i]) j += 1;
        if (j - i < 3) pieces.push(text.slice(i, j)); else changed = true;
        i = j;
      }
      text = pieces.join('');
      if (!changed) return text;
    }
  }
  function search(text, counts) {
    if (text.length === 0) return 0;
    const key = text + '|' + counts.join(',');
    if (memo.has(key)) return memo.get(key);
    const frequencies = Array(5).fill(0);
    for (const char of text) frequencies[colors.indexOf(char)] += 1;
    for (let c = 0; c < 5; c += 1) if (frequencies[c] > 0 && frequencies[c] + counts[c] < 3) return 6;
    let best = 6;
    for (let c = 0; c < 5; c += 1) {
      if (counts[c] === 0) continue;
      const color = colors[c], nextCounts = counts.slice(), generated = new Set();
      nextCounts[c] -= 1;
      for (let position = 0; position <= text.length; position += 1) {
        if (position > 0 && text[position - 1] === color) continue;
        const matches = position < text.length && text[position] === color;
        const splits = position > 0 && position < text.length && text[position - 1] === text[position] && text[position] !== color;
        if (!matches && !splits) continue;
        const next = shrink(text.slice(0, position) + color + text.slice(position));
        if (generated.has(next)) continue;
        generated.add(next);
        best = Math.min(best, 1 + search(next, nextCounts));
      }
    }
    memo.set(key, best);
    return best;
  }
  const answer = search(shrink(board), initial);
  return answer <= hand.length ? answer : -1;
}

const findMinStep = solve;
class Solution {
  findMinStep(board, hand) { return solve(board, hand); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMinStep };
