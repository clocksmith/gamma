"use strict";
// Hack2Hire 6a7f88b6d713d873ca7adc47 (Balance Ads Across Columns, variant 2) over an INFERRED spec; qualification unknown.
function solve(heights, k) {
  // Min-heap of column numbers ordered by (total, column); the smallest column is replaced in place.
  const columns = Array.from({length: k}, () => []), totals = new Float64Array(k), heap = new Int32Array(k);
  for (let column = 0; column < k; column++) heap[column] = column; // all totals 0: index order is a valid heap
  const less = (a, b) => totals[a] < totals[b] || (totals[a] === totals[b] && a < b);
  heights.forEach((height, index) => {
    const column = heap[0];
    columns[column].push(index);
    totals[column] += height;
    let i = 0;
    for (;;) { // sift the updated root down
      const l = 2 * i + 1, r = l + 1;
      let m = i;
      if (l < k && less(heap[l], heap[m])) m = l;
      if (r < k && less(heap[r], heap[m])) m = r;
      if (m === i) break;
      const t = heap[i]; heap[i] = heap[m]; heap[m] = t;
      i = m;
    }
  });
  return columns;
}
function assignColumns(heights, k) { return solve(heights, k); }
module.exports = solve;
module.exports.assignColumns = assignColumns;
