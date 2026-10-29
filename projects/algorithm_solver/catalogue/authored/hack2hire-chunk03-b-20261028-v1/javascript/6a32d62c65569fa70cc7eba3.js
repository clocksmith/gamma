"use strict";
// Hack2Hire 6a32d62c65569fa70cc7eba3 (Minimum Operations to Sort by Rotate and Flip) over an INFERRED spec; qualification unknown.

function solve(arr) {
  const n = arr.length;
  if (n === 1) return 0;
  const mod = (v) => ((v % n) + n) % n;
  let m = 0;
  for (let i = 1; i < n; i++) if (arr[i] < arr[m]) m = i;
  // state (r, f): f == 0 reads arr[(r + j) % n], f == 1 reads arr[(r - j) % n]
  const goals = new Set();
  let asc = true, desc = true;
  for (let j = 0; j < n - 1; j++) {
    if (!(arr[mod(m + j)] < arr[mod(m + j + 1)])) asc = false;
    if (!(arr[mod(m - j)] < arr[mod(m - j - 1)])) desc = false;
  }
  if (asc) goals.add(2 * m);
  if (desc) goals.add(2 * m + 1);
  if (!goals.size) return -1;
  const dist = new Int32Array(2 * n).fill(-1);
  const queue = new Int32Array(2 * n);
  let head = 0, tailIndex = 0;
  dist[0] = 0; queue[tailIndex++] = 0;
  while (head < tailIndex) {
    const state = queue[head++];
    if (goals.has(state)) return dist[state];
    const r = state >> 1, f = state & 1;
    const moves = f === 0 ? [2 * mod(r + 1), 2 * mod(r + n - 1) + 1] : [2 * mod(r - 1) + 1, 2 * mod(r + 1)];
    for (const next of moves) {
      if (dist[next] < 0) { dist[next] = dist[state] + 1; queue[tailIndex++] = next; }
    }
  }
  return -1;
}

function minOperations(arr) { return solve(arr); }

module.exports = solve;
module.exports.minOperations = minOperations;
