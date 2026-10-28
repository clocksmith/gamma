'use strict';

// 1724. Checking Existence of Edge Length Limited Paths (Medium).
// Specification: https://leetcode.com/problems/checking-existence-of-edge-length-limited-paths/description/
function solve(n, edgeList, queries) {
  const parent = [];
  for (let i = 0; i < n; i++) parent.push(i);
  function find(x) { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; }
  const edges = edgeList.slice().sort((a, b) => a[2] - b[2]);
  const indexed = queries.map((q, i) => [q[0], q[1], q[2], i]).sort((a, b) => a[2] - b[2]);
  const answer = new Array(queries.length).fill(false);
  let e = 0;
  for (const [u, v, limit, idx] of indexed) {
    while (e < edges.length && edges[e][2] < limit) {
      parent[find(edges[e][0])] = find(edges[e][1]);
      e++;
    }
    answer[idx] = find(u) === find(v);
  }
  return answer;
}
const distanceLimitedPathsExist = solve;
class Solution { distanceLimitedPathsExist(n, edgeList, queries) { return solve(n, edgeList, queries); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, distanceLimitedPathsExist };
