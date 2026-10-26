'use strict';

// 1697. Checking Existence of Edge Length Limited Paths: offline increasing-limit DSU sweep; O((E+Q) log(E+Q)+n) time and O(n+E+Q) space.

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

function solve(n, edgeList, queries) {
  const orderedEdges = edgeList.slice().sort((a, b) => a[2] - b[2]);
  const orderedQueries = queries.map(([first, second, limit], index) => [limit, first, second, index]);
  orderedQueries.sort((a, b) => a[0] - b[0]);
  const groups = new _DisjointSet(n);
  const answers = Array(queries.length).fill(false);
  let edgeIndex = 0;
  for (const [limit, first, second, index] of orderedQueries) {
    while (edgeIndex < orderedEdges.length && orderedEdges[edgeIndex][2] < limit) {
      groups.union(orderedEdges[edgeIndex][0], orderedEdges[edgeIndex][1]);
      edgeIndex += 1;
    }
    answers[index] = groups.find(first) === groups.find(second);
  }
  return answers;
}

const distanceLimitedPathsExist = solve;
class Solution {
  distanceLimitedPathsExist(n, edgeList, queries) { return solve(n, edgeList, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distanceLimitedPathsExist };
