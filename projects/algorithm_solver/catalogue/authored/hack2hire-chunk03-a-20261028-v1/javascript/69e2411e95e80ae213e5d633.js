"use strict";
// Hack2Hire 69e2411e95e80ae213e5d633 (Incremental String Tokenizer) over an INFERRED spec; qualification unknown.

function solve(text, tokenAlphabet) {
  const alpha = tokenAlphabet, m = alpha.length;
  const ids = new Map();
  alpha.forEach((token, i) => ids.set(token, i));
  let k = 0;
  while (k < m && alpha[k].length === 1) k++;
  const n = text.length;
  const val = new Array(n), nxt = new Array(n), prv = new Array(n), alive = new Array(n).fill(true);
  for (let i = 0; i < n; i++) { val[i] = ids.get(text[i]); nxt[i] = i + 1 < n ? i + 1 : -1; prv[i] = i - 1; }
  const pairs = new Map();
  const index = (p) => {
    const q = nxt[p];
    if (q === -1) return;
    const key = val[p] * m + val[q];
    let list = pairs.get(key);
    if (list === undefined) { list = []; pairs.set(key, list); }
    list.push(p);
  };
  for (let p = 0; p + 1 < n; p++) index(p);
  for (let j = k; j < m; j++) {
    const token = alpha[j];
    const keys = new Set(), positions = [];
    for (let s = 1; s < token.length; s++) {
      const a = ids.get(token.slice(0, s)), b = ids.get(token.slice(s));
      if (a === undefined || b === undefined || a >= j || b >= j) continue;
      const key = a * m + b;
      keys.add(key);
      const list = pairs.get(key);
      if (list !== undefined) { pairs.delete(key); for (const p of list) positions.push(p); }
    }
    if (positions.length === 0) continue;
    positions.sort((x, y) => x - y);
    let last = -1;
    for (const p of positions) {
      if (p === last || !alive[p]) continue;
      last = p;
      const q = nxt[p];
      if (q === -1 || !keys.has(val[p] * m + val[q])) continue;
      val[p] = j;
      alive[q] = false;
      const r = nxt[q];
      nxt[p] = r;
      if (r !== -1) prv[r] = p;
      index(p);
      if (prv[p] !== -1) index(prv[p]);
    }
  }
  const out = [];
  for (let p = n ? 0 : -1; p !== -1; p = nxt[p]) out.push(val[p]);
  return out;
}

function tokenize(text, tokenAlphabet) { return solve(text, tokenAlphabet); }

module.exports = solve;
module.exports.tokenize = tokenize;
