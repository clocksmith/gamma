'use strict';

// 2065. Maximum Path Quality of a Graph. Return-distance-pruned walk search; O(E log V+Delta^D) time, O(V+E+D) space, D<=10 in-domain. Inputs are preserved.

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

function solve(values, edges, maxTime) {
  const neighbors = Array.from({ length: values.length }, () => []);
  for (const [first, second, duration] of edges) {
    neighbors[first].push([second, duration]);
    neighbors[second].push([first, duration]);
  }
  const home = Array(values.length).fill(Infinity);
  home[0] = 0;
  const heap = new MinHeap((a, b) => a[0] < b[0]);
  heap.push([0, 0]);
  while (heap.size > 0) {
    const [elapsed, node] = heap.pop();
    if (elapsed !== home[node]) continue;
    for (const [target, duration] of neighbors[node]) {
      const following = elapsed + duration;
      if (following < home[target]) {
        home[target] = following;
        heap.push([following, target]);
      }
    }
  }
  const visits = Array(values.length).fill(0);
  visits[0] = 1;
  let answer = values[0];
  function search(node, elapsed, quality) {
    if (node === 0) answer = Math.max(answer, quality);
    for (const [target, duration] of neighbors[node]) {
      const following = elapsed + duration;
      if (following + home[target] > maxTime) continue;
      const extra = visits[target] === 0 ? values[target] : 0;
      visits[target] += 1;
      search(target, following, quality + extra);
      visits[target] -= 1;
    }
  }
  search(0, 0, values[0]);
  return answer;
}

const maximalPathQuality = solve;
class Solution {
  maximalPathQuality(values, edges, maxTime) { return solve(values, edges, maxTime); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximalPathQuality };
