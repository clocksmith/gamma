'use strict';

// 3970. Shortest Path With At Most K Consecutive Identical Characters.
// Specification: https://leetcode.com/problems/shortest-path-with-at-most-k-consecutive-identical-characters/description/
// O(k (n+m) log(nk)) time and O(nk+mk) worst-case space; Dijkstra on node/run-length states. Inputs are preserved.
function solve(n, edges, labels, k) {
  const graph = Array.from({ length: n }, () => []);
  for (const [from, to, weight] of edges) graph[from].push([to, weight]);
  const width = k + 1;
  const distance = new Float64Array(n * width).fill(Infinity);
  const heap = [];
  function push(entry) {
    let index = heap.length;
    heap.push(entry);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (heap[parent][0] <= entry[0]) break;
      heap[index] = heap[parent];
      index = parent;
    }
    heap[index] = entry;
  }
  function pop() {
    const first = heap[0], last = heap.pop();
    if (heap.length) {
      let index = 0;
      while (index * 2 + 1 < heap.length) {
        let child = index * 2 + 1;
        if (child + 1 < heap.length && heap[child + 1][0] < heap[child][0]) child++;
        if (last[0] <= heap[child][0]) break;
        heap[index] = heap[child];
        index = child;
      }
      heap[index] = last;
    }
    return first;
  }
  const settledRun = new Int32Array(n).fill(width);
  distance[1] = 0;
  push([0, 0, 1]);
  while (heap.length) {
    const [cost, node, run] = pop();
    if (distance[node * width + run] !== cost || settledRun[node] <= run) continue;
    settledRun[node] = run;
    if (node === n - 1) return cost;
    for (const [next, weight] of graph[node]) {
      const nextRun = labels[next] === labels[node] ? run + 1 : 1;
      if (nextRun > k || settledRun[next] <= nextRun) continue;
      const state = next * width + nextRun, nextCost = cost + weight;
      if (nextCost < distance[state]) {
        distance[state] = nextCost;
        push([nextCost, next, nextRun]);
      }
    }
  }
  return -1;
}

// Native judge method name is not established; canonical solve is the supported entry point.
if (typeof module !== 'undefined') module.exports = { solve };
