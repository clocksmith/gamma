"use strict";
// Hack2Hire 695ecf112e3ae59d53a81ea7 (Multithreaded Array Sort) over an INFERRED spec; qualification unknown.

function merge(x, y) {
  const out = new Array(x.length + y.length);
  let i = 0, j = 0, t = 0;
  while (i < x.length && j < y.length) out[t++] = y[j] < x[i] ? y[j++] : x[i++];
  while (i < x.length) out[t++] = x[i++];
  while (j < y.length) out[t++] = y[j++];
  return out;
}

function solve(nums, k) {
  const size = Math.floor(nums.length / k), extra = nums.length % k;
  let runs = [], start = 0;
  for (let t = 0; t < k; t++) {
    const length = size + (t < extra ? 1 : 0);
    if (length) runs.push(Array.from(Float64Array.from(nums.slice(start, start + length)).sort()));
    start += length;
  }
  while (runs.length > 1) {
    const next = [];
    for (let i = 0; i < runs.length; i += 2) next.push(i + 1 < runs.length ? merge(runs[i], runs[i + 1]) : runs[i]);
    runs = next;
  }
  return runs.length ? runs[0] : [];
}

function sortWithThreads(nums, k) { return solve(nums, k); }

module.exports = solve;
module.exports.sortWithThreads = sortWithThreads;
