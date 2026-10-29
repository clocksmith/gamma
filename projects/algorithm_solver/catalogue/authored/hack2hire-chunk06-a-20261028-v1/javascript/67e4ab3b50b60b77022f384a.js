"use strict";
// Hack2Hire 67e4ab3b50b60b77022f384a (Find Shortest Unique Prefix) over an INFERRED spec; qualification unknown.

function common(a, b) {
  const limit = Math.min(a.length, b.length);
  let k = 0;
  while (k < limit && a.charCodeAt(k) === b.charCodeAt(k)) k++;
  return k;
}

function solve(words) {
  const n = words.length, order = Array.from({length: n}, (_, i) => i);
  order.sort((x, y) => (words[x] < words[y] ? -1 : words[x] > words[y] ? 1 : 0));
  const need = new Int32Array(n).fill(1);
  for (let t = 0; t + 1 < n; t++) {
    const x = order[t], y = order[t + 1], k = common(words[x], words[y]) + 1;
    if (k > need[x]) need[x] = k;
    if (k > need[y]) need[y] = k;
  }
  return words.map((w, i) => w.slice(0, need[i]));
}

function shortestUniquePrefix(words) { return solve(words); }

module.exports = solve;
module.exports.shortestUniquePrefix = shortestUniquePrefix;
