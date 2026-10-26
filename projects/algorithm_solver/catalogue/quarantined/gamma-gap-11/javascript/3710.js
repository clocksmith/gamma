'use strict';

// 3710. Maximum Partition Factor.
// O(n^2 log n) time and O(n^2) space; the first odd-cycle threshold bounds two-color separation.
function solve(points) {
  const n = points.length;
  if (n === 2) return 0;
  const edges = [];
  for (let left = 0; left < n; left += 1) {
    for (let right = left + 1; right < n; right += 1) {
      const distance = Math.abs(points[left][0] - points[right][0]) + Math.abs(points[left][1] - points[right][1]);
      edges.push([distance, left, right]);
    }
  }
  edges.sort((left, right) => left[0] - right[0]);
  const parent = Array.from({ length: 2 * n }, (_, index) => index);
  const size = new Int32Array(2 * n).fill(1);
  function find(node) {
    while (parent[node] !== node) {
      parent[node] = parent[parent[node]];
      node = parent[node];
    }
    return node;
  }
  function unite(left, right) {
    left = find(left);
    right = find(right);
    if (left === right) return;
    if (size[left] < size[right]) [left, right] = [right, left];
    parent[right] = left;
    size[left] += size[right];
  }
  for (const [distance, left, right] of edges) {
    if (find(left) === find(right)) return distance;
    unite(left, right + n);
    unite(right, left + n);
  }
  return 0;
}

const maxPartitionFactor = solve;
class Solution {
  maxPartitionFactor(points) { return solve(points); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxPartitionFactor };
