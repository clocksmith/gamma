"use strict";

function pushMin(h, v) {
  h.push(v);
  let i = h.length - 1;
  while (i > 0) {
    const p = (i - 1) >> 1;
    if (h[p] <= h[i]) break;
    const t = h[p]; h[p] = h[i]; h[i] = t;
    i = p;
  }
}

function popMin(h) {
  const top = h[0];
  const last = h.pop();
  if (h.length > 0) {
    h[0] = last;
    let i = 0;
    const n = h.length;
    while (true) {
      let l = (i << 1) + 1, r = l + 1, b = i;
      if (l < n && h[l] < h[b]) b = l;
      if (r < n && h[r] < h[b]) b = r;
      if (b === i) break;
      const t = h[i]; h[i] = h[b]; h[b] = t;
      i = b;
    }
  }
  return top;
}

class MedianFinder {
  constructor() {
    this.lower = [];
    this.upper = [];
  }
  addNum(num) {
    pushMin(this.lower, -num);
    pushMin(this.upper, -popMin(this.lower));
    if (this.upper.length > this.lower.length) {
      pushMin(this.lower, -popMin(this.upper));
    }
  }
  findMedian() {
    if (this.lower.length > this.upper.length) return -this.lower[0];
    return (-this.lower[0] + this.upper[0]) / 2.0;
  }
}

function solve(operation_names, argument_lists) {
  const instance = new MedianFinder();
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i];
    const args = argument_lists[i];
    if (op === "addNum") {
      instance.addNum(args[0]);
      out.push(null);
    } else if (op === "findMedian") {
      out.push(instance.findMedian());
    } else {
      throw new Error("unknown operation");
    }
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.MedianFinder = MedianFinder;
