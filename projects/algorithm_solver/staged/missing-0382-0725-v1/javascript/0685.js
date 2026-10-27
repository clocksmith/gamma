'use strict';

// 685. Redundant Connection II. Separate the two-parent case from the cycle case; preserve every input edge.

class _DSU {
  constructor(n) { this.parent = Array.from({length: n}, (_, i) => i); this.size = Array(n).fill(1); }
  find(x) {
    while (this.parent[x] !== x) {
      this.parent[x] = this.parent[this.parent[x]];
      x = this.parent[x];
    }
    return x;
  }
  union(a, b) {
    a = this.find(a); b = this.find(b);
    if (a === b) return false;
    if (this.size[a] < this.size[b]) [a, b] = [b, a];
    this.parent[b] = a;
    this.size[a] += this.size[b];
    return true;
  }
}

function solve(edges) {
  const n = edges.length, parentEdge = Array(n + 1).fill(-1);
  let first = -1, second = -1;
  edges.forEach(([, target], index) => {
    if (parentEdge[target] !== -1) { first = parentEdge[target]; second = index; }
    else parentEdge[target] = index;
  });
  const dsu = new _DSU(n + 1);
  for (let index = 0; index < n; index += 1) {
    if (index === second) continue;
    const [source, target] = edges[index];
    if (!dsu.union(source, target)) return first !== -1 ? edges[first].slice() : [source, target];
  }
  return second !== -1 ? edges[second].slice() : [];
}

const findRedundantDirectedConnection = solve;
class Solution {
  findRedundantDirectedConnection(edges) { return solve(edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findRedundantDirectedConnection };
