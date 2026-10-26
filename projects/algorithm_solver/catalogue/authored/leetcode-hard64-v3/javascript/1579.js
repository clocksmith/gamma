'use strict';

// 1579. Remove Max Number of Edges to Keep Graph Fully Traversable: shared edges before private edges using two DSUs; O((n+E)*alpha(n)) time and O(n) space.

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
  const alice = new _DisjointSet(n);
  const bob = new _DisjointSet(n);
  let retained = 0;
  for (const [kind, first, second] of edges) {
    if (kind === 3) {
      const aliceAdded = alice.union(first - 1, second - 1);
      const bobAdded = bob.union(first - 1, second - 1);
      if (aliceAdded || bobAdded) retained += 1;
    }
  }
  for (const [kind, first, second] of edges) {
    if (kind === 1 && alice.union(first - 1, second - 1)) retained += 1;
    else if (kind === 2 && bob.union(first - 1, second - 1)) retained += 1;
  }
  return alice.components === 1 && bob.components === 1 ? edges.length - retained : -1;
}

const maxNumEdgesToRemove = solve;
class Solution {
  maxNumEdgesToRemove(n, edges) { return solve(n, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxNumEdgesToRemove };
