'use strict';

// 1489. Find Critical and Pseudo-Critical Edges in Minimum Spanning Tree: forced/excluded-edge Kruskal runs; O(E^2*alpha(n) + E log E) time and O(n+E) space.

class _DisjointSet {
  constructor(size) {
    this.parent = Array.from({ length: size }, (_, index) => index);
    this.weight = Array(size).fill(1);
    this.components = size;
  }

  find(node) {
    while (node !== this.parent[node]) {
      this.parent[node] = this.parent[this.parent[node]];
      node = this.parent[node];
    }
    return node;
  }

  union(first, second) {
    let left = this.find(first);
    let right = this.find(second);
    if (left === right) return false;
    if (this.weight[left] < this.weight[right]) [left, right] = [right, left];
    this.parent[right] = left;
    this.weight[left] += this.weight[right];
    this.components -= 1;
    return true;
  }
}

function solve(n, edges) {
  const ordered = edges.map(([first, second, weight], index) => [weight, first, second, index]);
  ordered.sort((a, b) => a[0] - b[0] || a[3] - b[3]);
  function spanning(skip = -1, force = -1) {
    const groups = new _DisjointSet(n);
    let total = 0;
    if (force >= 0) {
      const [first, second, weight] = edges[force];
      if (groups.union(first, second)) total += weight;
    }
    for (const [weight, first, second, index] of ordered) {
      if (index !== skip && groups.union(first, second)) total += weight;
    }
    return groups.components === 1 ? total : Infinity;
  }
  const baseline = spanning();
  const critical = [];
  const optional = [];
  for (let index = 0; index < edges.length; index += 1) {
    if (spanning(index) > baseline) critical.push(index);
    else if (spanning(-1, index) === baseline) optional.push(index);
  }
  return [critical, optional];
}

const findCriticalAndPseudoCriticalEdges = solve;
class Solution {
  findCriticalAndPseudoCriticalEdges(n, edges) { return solve(n, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findCriticalAndPseudoCriticalEdges };
