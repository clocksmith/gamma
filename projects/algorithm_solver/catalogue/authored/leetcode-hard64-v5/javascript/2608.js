'use strict';

// 2608. Shortest Cycle in a Graph. Breadth-first search from each vertex with non-parent edge detection; O(n*(n+m)) time and O(n+m) space. Inputs are preserved.

function solve(n, edges) {
  const graph = Array.from({ length: n }, () => []);
  for (const [first, second] of edges) {
    graph[first].push(second);
    graph[second].push(first);
  }
  let answer = n + 1;
  for (let start = 0; start < n; start += 1) {
    const distance = Array(n).fill(-1);
    const parent = Array(n).fill(-1);
    distance[start] = 0;
    const queue = [start];
    for (let head = 0; head < queue.length; head += 1) {
      const node = queue[head];
      for (const neighbor of graph[node]) {
        if (distance[neighbor] === -1) {
          distance[neighbor] = distance[node] + 1;
          parent[neighbor] = node;
          queue.push(neighbor);
        } else if (parent[node] !== neighbor) {
          answer = Math.min(answer, distance[node] + distance[neighbor] + 1);
        }
      }
    }
    if (answer === 3) return 3;
  }
  return answer <= n ? answer : -1;
}

const findShortestCycle = solve;
class Solution {
  findShortestCycle(n, edges) { return solve(n, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findShortestCycle };
