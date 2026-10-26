'use strict';

// 3123. Find Edges in Shortest Paths.
// Dijkstra from both endpoints identifies every edge on a shortest path; O((n+e) log n) time, O(n+e) space. Inputs are preserved.

class MinHeap {
  constructor(compare = (a, b) => a - b) {
    this.items = [];
    this.compare = compare;
  }
  push(value) {
    const items = this.items;
    let index = items.length;
    items.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (this.compare(items[parent], value) <= 0) break;
      items[index] = items[parent];
      index = parent;
    }
    items[index] = value;
  }
  pop() {
    const items = this.items;
    const answer = items[0];
    const last = items.pop();
    if (items.length === 0) return answer;
    let index = 0;
    while (2 * index + 1 < items.length) {
      let child = 2 * index + 1;
      if (child + 1 < items.length && this.compare(items[child + 1], items[child]) < 0) child += 1;
      if (this.compare(last, items[child]) <= 0) break;
      items[index] = items[child];
      index = child;
    }
    items[index] = last;
    return answer;
  }
}

function solve(n, edges) {
  const graph = Array.from({ length: n }, () => []);
  for (const [a, b, weight] of edges) { graph[a].push([b, weight]); graph[b].push([a, weight]); }
  function distances(start) {
    const result = Array(n).fill(Infinity), heap = new MinHeap((a, b) => a[0] - b[0]);
    result[start] = 0; heap.push([0, start]);
    while (heap.items.length > 0) {
      const [distance, node] = heap.pop();
      if (distance !== result[node]) continue;
      for (const [neighbor, weight] of graph[node]) {
        const candidate = distance + weight;
        if (candidate < result[neighbor]) { result[neighbor] = candidate; heap.push([candidate, neighbor]); }
      }
    }
    return result;
  }
  const first = distances(0), last = distances(n - 1), shortest = first[n - 1];
  if (shortest === Infinity) return edges.map(() => false);
  return edges.map(([a, b, weight]) => first[a] + weight + last[b] === shortest || first[b] + weight + last[a] === shortest);
}

const findAnswer = solve;
class Solution {
  findAnswer(n, edges) { return solve(n, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findAnswer };
