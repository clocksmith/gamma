"use strict";

function solve(queries, k) {
  const heap = [];
  function push(val) {
    heap.push(val);
    let i = heap.length - 1;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (heap[p] >= heap[i]) break;
      const tmp = heap[p];
      heap[p] = heap[i];
      heap[i] = tmp;
      i = p;
    }
  }
  function replaceTop(val) {
    heap[0] = val;
    let i = 0;
    const n = heap.length;
    while (true) {
      let l = (i << 1) + 1;
      let r = l + 1;
      let best = i;
      if (l < n && heap[l] > heap[best]) best = l;
      if (r < n && heap[r] > heap[best]) best = r;
      if (best === i) break;
      const tmp = heap[i];
      heap[i] = heap[best];
      heap[best] = tmp;
      i = best;
    }
  }
  const out = [];
  for (let i = 0; i < queries.length; i++) {
    const d = Math.abs(queries[i][0]) + Math.abs(queries[i][1]);
    if (heap.length < k) push(d);
    else if (d < heap[0]) replaceTop(d);
    out.push(heap.length === k ? heap[0] : -1);
  }
  return out;
}

function resultsArray(queries, k) {
  return solve(queries, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.resultsArray = resultsArray;
