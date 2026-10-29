"use strict";
// Original Hack2Hire 6987d34fdce67a3d5ecc12bd variant over an INFERRED specification; qualification unknown.
function solve(n, treeFrom, treeTo, x, y, z) {
  const adjacent = Array.from({length: n}, () => []);
  for (let i = 0; i < treeFrom.length; i++) { adjacent[treeFrom[i]].push(treeTo[i]); adjacent[treeTo[i]].push(treeFrom[i]); }
  const bfs = (source) => {
    const dist = new Array(n).fill(-1), queue = [source];
    dist[source] = 0;
    for (let head = 0; head < queue.length; head++) {
      const u = queue[head];
      for (const v of adjacent[u]) if (dist[v] < 0) { dist[v] = dist[u] + 1; queue.push(v); }
    }
    return dist;
  };
  const dx = bfs(x), dy = bfs(y), dz = bfs(z);
  let count = 0;
  for (let u = 0; u < n; u++) {
    const [a, b, c] = [dx[u], dy[u], dz[u]].sort((p, q) => p - q);
    if (a * a + b * b === c * c) count++;
  }
  return count;
}
function countPythagoreanNodes(n, treeFrom, treeTo, x, y, z) { return solve(n, treeFrom, treeTo, x, y, z); }
module.exports = solve;
module.exports.countPythagoreanNodes = countPythagoreanNodes;
