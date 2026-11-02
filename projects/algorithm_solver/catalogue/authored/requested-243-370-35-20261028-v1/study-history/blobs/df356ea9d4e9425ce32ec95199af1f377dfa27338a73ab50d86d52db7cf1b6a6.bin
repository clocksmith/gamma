"use strict";

function solve(s) {
  const cnt = new Map();
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    cnt.set(ch, (cnt.get(ch) || 0) + 1);
  }
  const odds = [];
  const half = [];
  for (const [ch, c] of cnt.entries()) {
    if (c & 1) odds.push(ch);
    for (let k = 0; k < (c >> 1); k++) half.push(ch);
  }
  if (odds.length > 1) return [];
  const mid = odds.length === 1 ? odds[0] : "";
  half.sort();
  const m = half.length;
  const used = new Uint8Array(m);
  const res = [];
  const cur = [];
  function backtrack() {
    if (cur.length === m) {
      const left = cur.join("");
      const right = cur.slice().reverse().join("");
      res.push(left + mid + right);
      return;
    }
    for (let i = 0; i < m; i++) {
      if (used[i]) continue;
      if (i > 0 && half[i] === half[i - 1] && !used[i - 1]) continue;
      used[i] = 1;
      cur.push(half[i]);
      backtrack();
      cur.pop();
      used[i] = 0;
    }
  }
  backtrack();
  return res;
}

function generatePalindromes(s) {
  return solve(s);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.generatePalindromes = generatePalindromes;
