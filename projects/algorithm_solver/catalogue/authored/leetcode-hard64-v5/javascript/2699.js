'use strict';

// 2699. Modify Graph Edge Weights. Two Dijkstra passes distribute the target slack over adjustable edges; O((n+m) log(n+m)) time and O(n+m) space. Inputs are preserved.

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
    const result = items[0];
    const value = items.pop();
    if (items.length === 0) return result;
    let index = 0;
    while (2 * index + 1 < items.length) {
      let child = 2 * index + 1;
      if (child + 1 < items.length && this.less(items[child + 1], items[child])) child += 1;
      if (!this.less(items[child], value)) break;
      items[index] = items[child];
      index = child;
    }
    items[index] = value;
    return result;
  }
}

function solve(n, edges, source, destination, target) {
  const result = edges.map(edge => edge.slice());
  const graph = Array.from({ length: n }, () => []);
  for (let index = 0; index < result.length; index += 1) {
    const [first, second] = result[index];
    graph[first].push([second, index]);
    graph[second].push([first, index]);
  }
  function shortest(baseline = null, slack = 0) {
    const distance = Array(n).fill(Infinity);
    distance[source] = 0;
    const heap = new MinHeap((a, b) => a[0] < b[0]);
    heap.push([0, source]);
    while (heap.size > 0) {
      const [elapsed, node] = heap.pop();
      if (elapsed !== distance[node]) continue;
      for (const [neighbor, index] of graph[node]) {
        let weight = result[index][2];
        if (weight === -1) {
          weight = 1;
          if (baseline !== null) {
            const proposed = slack + baseline[neighbor] - elapsed;
            if (proposed > 1) { weight = proposed; result[index][2] = weight; }
          }
        }
        const arrival = elapsed + weight;
        if (arrival < distance[neighbor]) {
          distance[neighbor] = arrival;
          heap.push([arrival, neighbor]);
        }
      }
    }
    return distance;
  }
  const baseline = shortest();
  const slack = target - baseline[destination];
  if (slack < 0) return [];
  const distance = shortest(baseline, slack);
  if (distance[destination] !== target) return [];
  for (const edge of result) if (edge[2] === -1) edge[2] = 1;
  return result;
}

const modifiedGraphEdges = solve;
class Solution {
  modifiedGraphEdges(n, edges, source, destination, target) { return solve(n, edges, source, destination, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, modifiedGraphEdges };
