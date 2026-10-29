"use strict";

function collapse(s) {
  let changed = true;
  while (changed) {
    changed = false;
    let i = 0;
    const n = s.length;
    while (i < n) {
      let j = i;
      while (j < n && s[j] === s[i]) j++;
      if (j - i >= 3) {
        s = s.slice(0, i) + s.slice(j);
        changed = true;
        break;
      }
      i = j;
    }
  }
  return s;
}

function solve(board, hand) {
  const b0 = collapse(board);
  const h0 = hand.split("").sort().join("");
  const q = [[b0, h0, 0]];
  const visited = new Set([b0 + "#" + h0]);
  let head = 0;
  while (head < q.length) {
    const [b, h, steps] = q[head++];
    if (b.length === 0) return steps;
    if (h.length === 0) continue;
    for (let hi = 0; hi < h.length; hi++) {
      const ch = h[hi];
      if (hi > 0 && h[hi] === h[hi - 1]) continue;
      const nh = h.slice(0, hi) + h.slice(hi + 1);
      for (let bi = 0; bi <= b.length; bi++) {
        if (bi > 0 && b[bi - 1] === ch) continue;
        let pick = false;
        if (bi < b.length && b[bi] === ch) pick = true;
        else if (bi > 0 && bi < b.length && b[bi - 1] === b[bi] && b[bi] !== ch) pick = true;
        if (!pick) continue;
        const nb = collapse(b.slice(0, bi) + ch + b.slice(bi));
        if (nb.length === 0) return steps + 1;
        const key = nb + "#" + nh;
        if (!visited.has(key)) {
          visited.add(key);
          q.push([nb, nh, steps + 1]);
        }
      }
    }
  }
  return -1;
}

function findMinStep(board, hand) {
  return solve(board, hand);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.findMinStep = findMinStep;
