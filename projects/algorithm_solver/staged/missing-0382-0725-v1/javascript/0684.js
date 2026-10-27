'use strict';

// 684. Redundant Connection.

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
  const dsu = new _DSU(edges.length + 1);
  for (const [a, b] of edges) if (!dsu.union(a, b)) return [a, b];
  return [];
}

const findRedundantConnection = solve;
class Solution {
  findRedundantConnection(edges) { return solve(edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findRedundantConnection };
