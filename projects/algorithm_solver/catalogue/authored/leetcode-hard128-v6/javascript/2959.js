'use strict';

// 2959. Number of Possible Sets of Closing Branches.
// Floyd-Warshall restricted to each surviving subset; O(2^n*n^3) time, O(n^2) space. Inputs are preserved.

function solve(n, maxDistance, roads) {
  const base = Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => i === j ? 0 : Infinity));
  for (const [a, b, weight] of roads) base[a][b] = base[b][a] = Math.min(base[a][b], weight);
  let answer = 0;
  for (let mask = 0; mask < 1 << n; mask += 1) {
    const nodes = [];
    for (let node = 0; node < n; node += 1) if ((mask >>> node) & 1) nodes.push(node);
    const distance = base.map(row => row.slice());
    for (const middle of nodes) for (const a of nodes) for (const b of nodes) distance[a][b] = Math.min(distance[a][b], distance[a][middle] + distance[middle][b]);
    let valid = true;
    for (const a of nodes) for (const b of nodes) if (distance[a][b] > maxDistance) valid = false;
    if (valid) answer += 1;
  }
  return answer;
}

const numberOfSets = solve;
class Solution {
  numberOfSets(n, maxDistance, roads) { return solve(n, maxDistance, roads); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfSets };
