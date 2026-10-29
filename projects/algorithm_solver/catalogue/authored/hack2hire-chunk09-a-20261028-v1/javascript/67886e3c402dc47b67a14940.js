"use strict";
// Hack2Hire 67886e3c402dc47b67a14940 (Windowed Average excluding Largest K) over an INFERRED spec; qualification unknown.

// Binary heap over parallel value/index arrays; less(a, b) orders (value, index) pairs.
class Heap {
  constructor(less) { this.v = []; this.i = []; this.less = less; }
  get size() { return this.v.length; }
  push(value, index) {
    const v = this.v, ix = this.i, less = this.less;
    let k = v.length;
    v.push(value); ix.push(index);
    while (k > 0) {
      const p = (k - 1) >> 1;
      if (!less(value, index, v[p], ix[p])) break;
      v[k] = v[p]; ix[k] = ix[p]; k = p;
    }
    v[k] = value; ix[k] = index;
  }
  pop() {
    const v = this.v, ix = this.i, less = this.less;
    const lastV = v.pop(), lastI = ix.pop();
    const n = v.length;
    if (n === 0) return;
    let k = 0;
    for (;;) {
      let c = 2 * k + 1;
      if (c >= n) break;
      if (c + 1 < n && less(v[c + 1], ix[c + 1], v[c], ix[c])) c += 1;
      if (!less(v[c], ix[c], lastV, lastI)) break;
      v[k] = v[c]; ix[k] = ix[c]; k = c;
    }
    v[k] = lastV; ix[k] = lastI;
  }
}

function solve(nums, windowSize, k) {
  const w = windowSize;
  const top = new Heap((a, ai, b, bi) => a < b || (a === b && ai < bi)); // k largest, smallest on top
  const rest = new Heap((a, ai, b, bi) => a > b || (a === b && ai > bi)); // others, largest on top
  const where = new Uint8Array(nums.length); // 1 = in top, 2 = in rest, 0 = gone
  let topSize = 0, topSum = 0, restSize = 0, windowSum = 0;
  const out = [];
  const cleanTop = () => { while (top.size && where[top.i[0]] !== 1) top.pop(); };
  const cleanRest = () => { while (rest.size && where[rest.i[0]] !== 2) rest.pop(); };
  for (let i = 0; i < nums.length; i++) {
    const v = nums[i];
    if (i >= w) {
      const j = i - w;
      windowSum -= nums[j];
      if (where[j] === 1) { topSize -= 1; topSum -= nums[j]; } else restSize -= 1;
      where[j] = 0;
    }
    windowSum += v;
    top.push(v, i); where[i] = 1; topSize += 1; topSum += v;
    cleanTop();
    const x = top.v[0], xi = top.i[0];
    top.pop();
    where[xi] = 2; topSize -= 1; topSum -= x; restSize += 1;
    rest.push(x, xi);
    while (topSize < k && restSize > 0) {
      cleanRest();
      const y = rest.v[0], yi = rest.i[0];
      rest.pop();
      where[yi] = 1; restSize -= 1; topSize += 1; topSum += y;
      top.push(y, yi);
    }
    if (i >= w - 1) {
      const num = windowSum - topSum, den = w - k;
      let q = Math.floor(num / den);
      const r = num - q * den; // exact: |num| < 2**53
      if (r < 0) q -= 1; else if (r >= den) q += 1;
      out.push(q);
    }
  }
  return out;
}

function windowAverages(nums, windowSize, k) { return solve(nums, windowSize, k); }

module.exports = solve;
module.exports.windowAverages = windowAverages;
