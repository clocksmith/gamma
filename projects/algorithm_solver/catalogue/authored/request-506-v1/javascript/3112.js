// Original implementation. Contract: https://leetcode.com/problems/minimum-time-to-visit-disappearing-nodes/
"use strict";

function solve(n, edges, disappear) {
  const adjacency = Array.from({ length: n }, () => []);
  for (const [u, v, weight] of edges) {
    adjacency[u].push([v, weight]);
    adjacency[v].push([u, weight]);
  }
  const heap = [];
  function push(item) {
    heap.push(item);
    let index = heap.length - 1;
    while (index > 0) {
      const parent = (index - 1) >> 1;
      if (heap[parent][0] <= item[0]) break;
      heap[index] = heap[parent];
      index = parent;
    }
    heap[index] = item;
  }
  function pop() {
    const minimum = heap[0];
    const last = heap.pop();
    if (heap.length > 0) {
      let index = 0;
      while (2 * index + 1 < heap.length) {
        let child = 2 * index + 1;
        if (child + 1 < heap.length && heap[child + 1][0] < heap[child][0]) child++;
        if (heap[child][0] >= last[0]) break;
        heap[index] = heap[child];
        index = child;
      }
      heap[index] = last;
    }
    return minimum;
  }
  const distance = Array(n).fill(Infinity);
  distance[0] = 0;
  push([0, 0]);
  while (heap.length > 0) {
    const [time, node] = pop();
    if (time !== distance[node]) continue;
    for (const [next, weight] of adjacency[node]) {
      const arrival = time + weight;
      if (arrival < distance[next] && arrival < disappear[next]) {
        distance[next] = arrival;
        push([arrival, next]);
      }
    }
  }
  return distance.map(value => value === Infinity ? -1 : value);
}

module.exports = solve;
