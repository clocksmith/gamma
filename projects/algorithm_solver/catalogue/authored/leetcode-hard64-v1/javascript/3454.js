'use strict';

// 3454. Separate Squares II: sweep union-covered horizontal strips with a segment tree.
// O(n log n) time and O(n) auxiliary space. Inputs are preserved.
function solve(squares) {
  const endpointSet = new Set();
  for (const [x, , side] of squares) {
    endpointSet.add(x);
    endpointSet.add(x + side);
  }
  const coordinates = Array.from(endpointSet).sort((a, b) => a - b);
  const indexOf = new Map(coordinates.map((value, index) => [value, index]));
  const segments = coordinates.length - 1;
  const cover = new Int32Array(4 * segments);
  const length = new Float64Array(4 * segments);
  const events = [];
  for (const [x, y, side] of squares) {
    const first = indexOf.get(x);
    const last = indexOf.get(x + side) - 1;
    events.push([y, 1, first, last], [y + side, -1, first, last]);
  }
  events.sort((a, b) => a[0] - b[0]);
  function update(node, left, right, first, last, change) {
    if (first <= left && right <= last) {
      cover[node] += change;
    } else {
      const middle = Math.floor((left + right) / 2);
      if (first <= middle) update(2 * node, left, middle, first, last, change);
      if (last > middle) update(2 * node + 1, middle + 1, right, first, last, change);
    }
    if (cover[node] > 0) length[node] = coordinates[right + 1] - coordinates[left];
    else if (left === right) length[node] = 0;
    else length[node] = length[2 * node] + length[2 * node + 1];
  }
  const strips = [];
  let total = 0;
  let previousY = events[0][0];
  let position = 0;
  while (position < events.length) {
    const y = events[position][0];
    if (y > previousY) {
      const width = length[1];
      strips.push([previousY, y, width]);
      total += (y - previousY) * width;
    }
    while (position < events.length && events[position][0] === y) {
      const [, change, first, last] = events[position++];
      update(1, 0, segments - 1, first, last, change);
    }
    previousY = y;
  }
  let accumulated = 0;
  for (const [bottom, top, width] of strips) {
    const area = (top - bottom) * width;
    if (width > 0 && 2 * (accumulated + area) >= total) {
      return bottom + (total - 2 * accumulated) / (2 * width);
    }
    accumulated += area;
  }
  return previousY;
}

const separateSquares = solve;
class Solution {
  separateSquares(squares) { return solve(squares); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, separateSquares };
