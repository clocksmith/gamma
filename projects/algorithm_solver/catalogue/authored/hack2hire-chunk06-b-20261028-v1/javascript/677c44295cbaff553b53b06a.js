"use strict";
// Hack2Hire 677c44295cbaff553b53b06a (Keyboard Jump Challenge) over an INFERRED spec; qualification unknown.

function solve(keyboard, maxDistance, word) {
  const m = keyboard.length, n = keyboard[0].length, cells = new Map();
  for (let r = 0; r < m; r++) for (let c = 0; c < n; c++) {
    const ch = keyboard[r][c];
    if (!cells.has(ch)) cells.set(ch, []);
    cells.get(ch).push(r * n + c);
  }
  for (const ch of word) if (!cells.has(ch)) return false;
  const big = m + n + 1, memo = new Map(), dist = new Int32Array(m * n);
  let current = cells.get(word[0]);
  for (let w = 1; w < word.length; w++) {
    const ch = word[w], key = current.join(",") + "|" + ch;
    let next = memo.get(key);
    if (next === undefined) {
      dist.fill(big);
      for (const cell of current) dist[cell] = 0;
      for (let r = 0; r < m; r++) for (let c = 0; c < n; c++) {
        const i = r * n + c;
        if (r && dist[i - n] + 1 < dist[i]) dist[i] = dist[i - n] + 1;
        if (c && dist[i - 1] + 1 < dist[i]) dist[i] = dist[i - 1] + 1;
      }
      for (let r = m - 1; r >= 0; r--) for (let c = n - 1; c >= 0; c--) {
        const i = r * n + c;
        if (r + 1 < m && dist[i + n] + 1 < dist[i]) dist[i] = dist[i + n] + 1;
        if (c + 1 < n && dist[i + 1] + 1 < dist[i]) dist[i] = dist[i + 1] + 1;
      }
      next = cells.get(ch).filter((cell) => dist[cell] <= maxDistance);
      memo.set(key, next);
    }
    current = next;
    if (!current.length) return false;
  }
  return true;
}

function canTypeWord(keyboard, maxDistance, word) { return solve(keyboard, maxDistance, word); }

module.exports = solve;
module.exports.canTypeWord = canTypeWord;
