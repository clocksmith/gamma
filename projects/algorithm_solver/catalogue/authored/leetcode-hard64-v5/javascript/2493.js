'use strict';

// 2493. Divide Nodes Into the Maximum Number of Groups. Reject odd cycles and maximize breadth-first layers in each component; O(n*(n+m)) time and O(n+m) space. Inputs are preserved.

function solve(n, edges) {
  const graph = Array.from({ length: n }, () => []);
  for (const [first, second] of edges) {
    graph[first - 1].push(second - 1);
    graph[second - 1].push(first - 1);
  }
  const color = Array(n).fill(-1);
  let answer = 0;
  for (let start = 0; start < n; start += 1) {
    if (color[start] !== -1) continue;
    const component = [start];
    color[start] = 0;
    for (let head = 0; head < component.length; head += 1) {
      const node = component[head];
      for (const neighbor of graph[node]) {
        if (color[neighbor] === -1) {
          color[neighbor] = color[node] ^ 1;
          component.push(neighbor);
        } else if (color[neighbor] === color[node]) {
          return -1;
        }
      }
    }
    let largest = 1;
    for (const root of component) {
      const distance = Array(n).fill(-1);
      distance[root] = 0;
      const queue = [root];
      for (let head = 0; head < queue.length; head += 1) {
        const node = queue[head];
        for (const neighbor of graph[node]) {
          if (distance[neighbor] !== -1) continue;
          distance[neighbor] = distance[node] + 1;
          queue.push(neighbor);
        }
      }
      largest = Math.max(largest, distance[queue[queue.length - 1]] + 1);
    }
    answer += largest;
  }
  return answer;
}

const magnificentSets = solve;
class Solution {
  magnificentSets(n, edges) { return solve(n, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, magnificentSets };
