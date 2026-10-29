"use strict";
// Hack2Hire 67eae60e4c9bb801bfd0ef48 (Rearrange Houses in Neighborhoods) over an INFERRED spec; qualification unknown.

// Max-heap of exact integer keys copies * 2^30 + (2^30 - number): more copies first, smaller number on ties.
// copies <= 2e5 < 2^18 and 1 <= number <= 1e9 < 2^30, so every key stays below 2^48 and is exact in a double.
const SHIFT = 1073741824;

function heapPush(h, key) {
  let i = h.length;
  h.push(key);
  while (i > 0) {
    const p = (i - 1) >> 1;
    if (h[p] >= key) break;
    h[i] = h[p]; i = p;
  }
  h[i] = key;
}

function heapPop(h) {
  const top = h[0], last = h.pop(), n = h.length;
  if (n) {
    let i = 0;
    for (;;) {
      let c = 2 * i + 1;
      if (c >= n) break;
      if (c + 1 < n && h[c + 1] > h[c]) c++;
      if (h[c] <= last) break;
      h[i] = h[c]; i = c;
    }
    h[i] = last;
  }
  return top;
}

function solve(houses) {
  const copies = new Map();
  for (const row of houses) for (const v of row) copies.set(v, (copies.get(v) || 0) + 1);
  const heap = [];
  for (const [v, c] of copies) heapPush(heap, c * SHIFT + (SHIFT - v));
  const out = [];
  for (const row of houses) {
    const need = row.length;
    if (need > heap.length) return [];
    const taken = [];
    for (let i = 0; i < need; i++) taken.push(heapPop(heap));
    const numbers = [];
    for (const key of taken) {
      const c = Math.floor(key / SHIFT), v = SHIFT - (key - c * SHIFT);
      numbers.push(v);
      if (c > 1) heapPush(heap, key - SHIFT);
    }
    out.push(numbers.sort((a, b) => a - b));
  }
  return out;
}

function rearrangeHouses(houses) { return solve(houses); }

module.exports = solve;
module.exports.rearrangeHouses = rearrangeHouses;
