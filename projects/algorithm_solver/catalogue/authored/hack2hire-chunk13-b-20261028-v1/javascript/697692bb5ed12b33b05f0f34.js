"use strict";
// Hack2Hire 697692bb5ed12b33b05f0f34 (Shipping Route Cost Paths, variant 3 of 3) over an INFERRED spec; qualification unknown.

function solve(routes, source, target) {
  if (source === target) return 0;
  const adjacency = new Map();
  for (const route of routes) {
    const [a, b, , cost] = route.split(":");
    if (!adjacency.has(a)) adjacency.set(a, []);
    adjacency.get(a).push([b, Number(cost)]);
  }
  const best = new Map([[source, 0]]);
  const heap = [[0, source]]; // binary min-heap on distance
  const push = (item) => {
    heap.push(item);
    for (let i = heap.length - 1; i > 0;) {
      const p = (i - 1) >> 1;
      if (heap[p][0] <= heap[i][0]) break;
      [heap[p], heap[i]] = [heap[i], heap[p]]; i = p;
    }
  };
  const pop = () => {
    const top = heap[0], last = heap.pop();
    if (heap.length) {
      heap[0] = last;
      for (let i = 0; ;) {
        const l = 2 * i + 1, r = l + 1;
        let m = i;
        if (l < heap.length && heap[l][0] < heap[m][0]) m = l;
        if (r < heap.length && heap[r][0] < heap[m][0]) m = r;
        if (m === i) break;
        [heap[m], heap[i]] = [heap[i], heap[m]]; i = m;
      }
    }
    return top;
  };
  while (heap.length) {
    const [dist, node] = pop();
    if (node === target) return dist;
    if (dist > best.get(node)) continue;
    for (const [next, cost] of adjacency.get(node) || []) {
      const nd = dist + cost;
      if (!best.has(next) || nd < best.get(next)) { best.set(next, nd); push([nd, next]); }
    }
  }
  return -1;
}

function cheapestShippingCost(routes, source, target) { return solve(routes, source, target); }

module.exports = solve;
module.exports.cheapestShippingCost = cheapestShippingCost;
