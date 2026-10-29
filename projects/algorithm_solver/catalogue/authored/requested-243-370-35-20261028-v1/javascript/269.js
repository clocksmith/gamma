"use strict";

function solve(words) {
  const charSet = new Set();
  for (let i = 0; i < words.length; i++) {
    for (let j = 0; j < words[i].length; j++) charSet.add(words[i][j]);
  }
  const chars = Array.from(charSet).sort();
  const adj = new Map();
  const indeg = new Map();
  for (const c of chars) {
    adj.set(c, new Set());
    indeg.set(c, 0);
  }
  for (let i = 0; i < words.length - 1; i++) {
    const w1 = words[i], w2 = words[i + 1];
    if (w1.length > w2.length && w1.startsWith(w2)) return "";
    const len = Math.min(w1.length, w2.length);
    for (let j = 0; j < len; j++) {
      const a = w1[j], b = w2[j];
      if (a !== b) {
        if (!adj.get(a).has(b)) {
          adj.get(a).add(b);
          indeg.set(b, indeg.get(b) + 1);
        }
        break;
      }
    }
  }
  const q = chars.filter((c) => indeg.get(c) === 0);
  const out = [];
  while (q.length > 0) {
    q.sort();
    const u = q.shift();
    out.push(u);
    const nb = Array.from(adj.get(u)).sort();
    for (const v of nb) {
      indeg.set(v, indeg.get(v) - 1);
      if (indeg.get(v) === 0) q.push(v);
    }
  }
  return out.length === chars.length ? out.join("") : "";
}

function alienOrder(words) {
  return solve(words);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.alienOrder = alienOrder;
