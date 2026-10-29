"use strict";
// Hack2Hire 68c8719bdf5a6365aa774b15 (Find Anagram in String) over an INFERRED spec; qualification unknown.

const POW = Array.from({length: 26}, (_, i) => 51 ** (i % 7));

function key(parts) {
  return parts[0] + "," + parts[1] + "," + parts[2] + "," + parts[3];
}

function signature(word) {
  const parts = [0, 0, 0, 0];
  for (let k = 0; k < word.length; k++) {
    const i = word.charCodeAt(k) - 97;
    parts[Math.floor(i / 7)] += POW[i];
  }
  return key(parts);
}

function solve(words, s) {
  const byLength = new Map();
  words.forEach((w, index) => {
    if (!byLength.has(w.length)) byLength.set(w.length, new Map());
    const table = byLength.get(w.length), sig = signature(w);
    if (!table.has(sig)) table.set(sig, []);
    table.get(sig).push(index);
  });
  let best = -1;
  const codes = Array.from(s, (c) => c.charCodeAt(0) - 97);
  for (const [length, table] of byLength) {
    if (length > codes.length) continue;
    const parts = [0, 0, 0, 0];
    for (let i = 0; i < length; i++) parts[Math.floor(codes[i] / 7)] += POW[codes[i]];
    let i = length;
    for (;;) {
      const k = key(parts), hit = table.get(k);
      if (hit !== undefined) {
        for (const index of hit) if (best < 0 || index < best) best = index;
        table.delete(k);
        if (table.size === 0) break;
      }
      if (i === codes.length) break;
      let c = codes[i];
      parts[Math.floor(c / 7)] += POW[c];
      c = codes[i - length];
      parts[Math.floor(c / 7)] -= POW[c];
      i++;
    }
  }
  return best < 0 ? "" : words[best];
}

function firstAnagramWord(words, s) { return solve(words, s); }

module.exports = solve;
module.exports.firstAnagramWord = firstAnagramWord;
