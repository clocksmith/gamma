'use strict';

// 4018. Total Sum of Interaction Cost in Tree Groups II.
// Specification: https://leetcode.com/problems/total-sum-of-interaction-cost-in-tree-groups-ii/description/
// O(n log n) expected time and O(n) live auxiliary space; small-to-large map merging. Inputs are preserved.
function solve(n, edges, group) {
  const graph = Array.from({ length: n }, () => []);
  for (const [left, right] of edges) { graph[left].push(right); graph[right].push(left); }
  const parent = new Int32Array(n).fill(-1);
  const depth = new Int32Array(n);
  const order = [0];
  parent[0] = 0;
  for (let index = 0; index < order.length; index++) {
    const node = order[index];
    for (const next of graph[node]) {
      if (next === parent[node]) continue;
      parent[next] = node;
      depth[next] = depth[node] + 1;
      order.push(next);
    }
  }
  const bags = new Array(n);
  let answer = 0;
  for (let index = order.length - 1; index >= 0; index--) {
    const node = order[index];
    let bag = new Map([[group[node], [1, depth[node]]]]);
    for (const child of graph[node]) {
      if (parent[child] !== node || child === node) continue;
      let other = bags[child];
      if (bag.size < other.size) [bag, other] = [other, bag];
      for (const [label, [count, depthSum]] of other) {
        const previous = bag.get(label);
        if (previous) {
          answer += previous[0] * depthSum + count * previous[1] - 2 * depth[node] * previous[0] * count;
          previous[0] += count;
          previous[1] += depthSum;
        } else bag.set(label, [count, depthSum]);
      }
      bags[child] = null;
    }
    bags[node] = bag;
  }
  return answer;
}

// Native judge method name is not established; canonical solve is the supported entry point.
if (typeof module !== 'undefined') module.exports = { solve };
