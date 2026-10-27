'use strict';

// 3650. Minimum Cost Path with Edge Reversals.
// Specification: https://leetcode.com/problems/minimum-cost-path-with-edge-reversals/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O((n + e) log(n + e)) time, O(n + e) space; a positive-weight optimal path never revisits a vertex.
// Inputs are not modified.

class MinHeap {
  constructor(compare = (a, b) => a - b) { this.data = []; this.compare = compare; }
  get size() { return this.data.length; }
  peek() { return this.data[0]; }
  push(value) {
    const data = this.data;
    let index = data.length;
    data.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (this.compare(data[parent], value) <= 0) break;
      data[index] = data[parent];
      index = parent;
    }
    data[index] = value;
  }
  pop() {
    const data = this.data;
    if (data.length === 0) return undefined;
    const result = data[0];
    const last = data.pop();
    if (data.length === 0) return result;
    let index = 0;
    while (2 * index + 1 < data.length) {
      let child = 2 * index + 1;
      if (child + 1 < data.length && this.compare(data[child + 1], data[child]) < 0) child++;
      if (this.compare(last, data[child]) <= 0) break;
      data[index] = data[child];
      index = child;
    }
    data[index] = last;
    return result;
  }
}

function solve(n, edges) {
  const graph = Array.from({ length: n }, () => []);
  for (const [source, target, weight] of edges) { graph[source].push([target, weight]); graph[target].push([source, 2 * weight]); }
  const distance = new Array(n).fill(Infinity), heap = new MinHeap((a, b) => a[0] - b[0]);
  distance[0] = 0; heap.push([0, 0]);
  while (heap.size) {
    const [cost, node] = heap.pop();
    if (cost !== distance[node]) continue;
    if (node === n - 1) return cost;
    for (const [target, weight] of graph[node]) {
      const following = cost + weight;
      if (following < distance[target]) { distance[target] = following; heap.push([following, target]); }
    }
  }
  return -1;
}

const minCost = solve;
class Solution {
  minCost(n, edges) { return solve(n, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCost };
