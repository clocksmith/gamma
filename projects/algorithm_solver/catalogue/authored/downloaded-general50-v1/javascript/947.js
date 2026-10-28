'use strict';

// 947. Most Stones Removed with Same Row or Column (Medium).
// Specification: https://leetcode.com/problems/most-stones-removed-with-same-row-or-column/description/
function solve(stones) {
  const parent = stones.map((_, i) => i);
  function find(x) { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; }
  function union(a, b) { parent[find(a)] = find(b); }
  for (let i = 0; i < stones.length; i++) {
    for (let j = i + 1; j < stones.length; j++) {
      if (stones[i][0] === stones[j][0] || stones[i][1] === stones[j][1]) union(i, j);
    }
  }
  const components = new Set(stones.map((_, i) => find(i)));
  return stones.length - components.size;
}
const removeStones = solve;
class Solution { removeStones(stones) { return solve(stones); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeStones };
