"use strict";

function lowerBound(arr, target) {
  let lo = 0, hi = arr.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid] < target) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

function solve(colors, queries) {
  const arr = colors.slice();
  const n = arr.length;
  const bitCnt = new Int32Array(n + 2);
  const bitSum = new Float64Array(n + 2);

  function bitAdd(len, delta) {
    let idx = len;
    const val = len * delta;
    while (idx <= n + 1) {
      bitCnt[idx] += delta;
      bitSum[idx] += val;
      idx += idx & -idx;
    }
  }

  function bitQuery(idx) {
    let c = 0, s = 0;
    while (idx > 0) {
      c += bitCnt[idx];
      s += bitSum[idx];
      idx -= idx & -idx;
    }
    return [c, s];
  }

  const cuts = [];
  for (let i = 0; i < n; i++) {
    if (arr[i] === arr[(i + 1) % n]) cuts.push(i);
  }
  for (let j = 0; j < cuts.length; j++) {
    const prev = cuts[(j - 1 + cuts.length) % cuts.length];
    const cur = cuts[j];
    let dist = (cur - prev + n) % n;
    if (dist === 0) dist = n;
    bitAdd(dist, 1);
  }

  function insertCut(pos) {
    const idx = lowerBound(cuts, pos);
    if (idx < cuts.length && cuts[idx] === pos) return;
    if (cuts.length === 0) {
      cuts.push(pos);
      bitAdd(n, 1);
      return;
    }
    const prev = idx > 0 ? cuts[idx - 1] : cuts[cuts.length - 1];
    const nxt = idx < cuts.length ? cuts[idx] : cuts[0];
    let oldD = (nxt - prev + n) % n;
    if (oldD === 0) oldD = n;
    bitAdd(oldD, -1);
    const d1 = (pos - prev + n) % n;
    const d2 = (nxt - pos + n) % n;
    bitAdd(d1, 1);
    bitAdd(d2, 1);
    cuts.splice(idx, 0, pos);
  }

  function removeCut(pos) {
    const idx = lowerBound(cuts, pos);
    if (idx === cuts.length || cuts[idx] !== pos) return;
    if (cuts.length === 1) {
      cuts.pop();
      bitAdd(n, -1);
      return;
    }
    const prev = idx > 0 ? cuts[idx - 1] : cuts[cuts.length - 1];
    const nxt = idx + 1 < cuts.length ? cuts[idx + 1] : cuts[0];
    const d1 = (pos - prev + n) % n;
    const d2 = (nxt - pos + n) % n;
    bitAdd(d1, -1);
    bitAdd(d2, -1);
    let newD = (nxt - prev + n) % n;
    if (newD === 0) newD = n;
    bitAdd(newD, 1);
    cuts.splice(idx, 1);
  }

  const out = [];
  for (let qi = 0; qi < queries.length; qi++) {
    const q = queries[qi];
    if (q[0] === 1) {
      const sz = q[1];
      if (cuts.length === 0) {
        out.push(n);
      } else {
        const [totC, totS] = bitQuery(n);
        const [loC, loS] = bitQuery(sz - 1);
        const c = totC - loC;
        const s = totS - loS;
        out.push(s - (sz - 1) * c);
      }
    } else {
      const idx = q[1], col = q[2];
      if (arr[idx] === col) continue;
      arr[idx] = col;
      const p1 = (idx - 1 + n) % n;
      for (const p of [p1, idx]) {
        if (arr[p] === arr[(p + 1) % n]) insertCut(p);
        else removeCut(p);
      }
    }
  }
  return out;
}

function numberOfAlternatingGroups(colors, queries) {
  return solve(colors, queries);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.numberOfAlternatingGroups = numberOfAlternatingGroups;
