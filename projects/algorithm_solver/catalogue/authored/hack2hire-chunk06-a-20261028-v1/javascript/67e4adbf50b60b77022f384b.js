"use strict";
// Hack2Hire 67e4adbf50b60b77022f384b (Find Middle Course, variant 2 of 2) over an INFERRED spec; qualification unknown.

const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

function solve(pairs) {
  const index = new Map(), names = [];
  for (const pair of pairs) for (const name of pair) if (!index.has(name)) { index.set(name, names.length); names.push(name); }
  const n = names.length, out = Array.from({length: n}, () => []), remaining = new Int32Array(n);
  for (const [a, b] of pairs) { out[index.get(a)].push(index.get(b)); remaining[index.get(b)]++; }
  const order = [], up = new Array(n).fill(0n), down = new Array(n).fill(0n);
  for (let v = 0; v < n; v++) if (remaining[v] === 0) { order.push(v); up[v] = 1n; }
  for (let k = 0; k < order.length; k++) {
    const v = order[k];
    for (const w of out[v]) { up[w] |= up[v] << 1n; if (--remaining[w] === 0) order.push(w); }
  }
  for (let k = order.length - 1; k >= 0; k--) {
    const v = order[k];
    if (!out[v].length) down[v] = 1n;
    for (const w of out[v]) down[v] |= down[w] << 1n;
  }
  const middles = [];
  for (let v = 0; v < n; v++) if ((up[v] & (down[v] | (down[v] >> 1n))) !== 0n) middles.push(names[v]);
  return middles.sort(cmp);
}

function findMiddleCourses(pairs) { return solve(pairs); }

module.exports = solve;
module.exports.findMiddleCourses = findMiddleCourses;
