'use strict';

// 1548. The Most Similar Path in a Graph: backward path dynamic programming and deterministic reconstruction.
// O(L * (n + E)) time and O(L * n + E) space. Inputs are preserved.
function solve(n, roads, names, targetPath) {
  const adjacency = Array.from({ length: n }, () => []);
  for (const [first, second] of roads) {
    adjacency[first].push(second);
    adjacency[second].push(first);
  }
  const length = targetPath.length;
  if (length === 0) return [];
  const choices = Array.from({ length }, () => new Int32Array(n).fill(-1));
  let cost = names.map(name => name === targetPath[length - 1] ? 0 : 1);
  for (let position = length - 2; position >= 0; position -= 1) {
    const following = Array(n).fill(length + 1);
    for (let node = 0; node < n; node += 1) {
      let bestNode = -1;
      let bestCost = length + 1;
      for (const neighbor of adjacency[node]) {
        if (cost[neighbor] < bestCost || (cost[neighbor] === bestCost && neighbor < bestNode)) {
          bestNode = neighbor;
          bestCost = cost[neighbor];
        }
      }
      if (bestNode >= 0) {
        following[node] = bestCost + (names[node] === targetPath[position] ? 0 : 1);
        choices[position][node] = bestNode;
      }
    }
    cost = following;
  }
  let current = 0;
  for (let node = 1; node < n; node += 1) {
    if (cost[node] < cost[current]) current = node;
  }
  if (cost[current] > length) return [];
  const answer = [current];
  for (let position = 0; position + 1 < length; position += 1) {
    current = choices[position][current];
    answer.push(current);
  }
  return answer;
}

const mostSimilar = solve;
class Solution {
  mostSimilar(n, roads, names, targetPath) { return solve(n, roads, names, targetPath); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mostSimilar };
