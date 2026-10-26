'use strict';

// 2203. Minimum Weighted Subgraph With the Required Paths. Three Dijkstra runs and a shared meeting vertex; O((V+E) log V) time and O(V+E) space. Inputs are preserved.

class MinHeap {
  constructor(less) {
    this.items = [];
    this.less = less;
  }
  get size() { return this.items.length; }
  peek() { return this.items[0]; }
  push(value) {
    const items = this.items;
    let index = items.length;
    items.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (!this.less(value, items[parent])) break;
      items[index] = items[parent];
      index = parent;
    }
    items[index] = value;
  }
  pop() {
    const items = this.items;
    const first = items[0];
    const last = items.pop();
    if (items.length > 0) {
      let index = 0;
      while (index * 2 + 1 < items.length) {
        let child = index * 2 + 1;
        if (child + 1 < items.length && this.less(items[child + 1], items[child])) child += 1;
        if (!this.less(items[child], last)) break;
        items[index] = items[child];
        index = child;
      }
      items[index] = last;
    }
    return first;
  }
}

function solve(n, edges, src1, src2, dest) {
  const forward = Array.from({ length: n }, () => []);
  const backward = Array.from({ length: n }, () => []);
  for (const [source, target, weight] of edges) {
    forward[source].push([target, weight]);
    backward[target].push([source, weight]);
  }
  function distances(start, neighbors) {
    const best = Array(n).fill(Infinity);
    best[start] = 0;
    const heap = new MinHeap((a, b) => a[0] < b[0]);
    heap.push([0, start]);
    while (heap.size > 0) {
      const [cost, node] = heap.pop();
      if (cost !== best[node]) continue;
      for (const [target, weight] of neighbors[node]) {
        const candidate = cost + weight;
        if (candidate < best[target]) {
          best[target] = candidate;
          heap.push([candidate, target]);
        }
      }
    }
    return best;
  }
  const first = distances(src1, forward);
  const second = distances(src2, forward);
  const finish = distances(dest, backward);
  let answer = Infinity;
  for (let node = 0; node < n; node += 1) answer = Math.min(answer, first[node] + second[node] + finish[node]);
  return answer === Infinity ? -1 : answer;
}

const minimumWeight = solve;
class Solution {
  minimumWeight(n, edges, src1, src2, dest) { return solve(n, edges, src1, src2, dest); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumWeight };
