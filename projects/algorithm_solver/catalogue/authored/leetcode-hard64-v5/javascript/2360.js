'use strict';

// 2360. Longest Cycle in a Graph. Timestamp each walk and recognize cycles within its own visit interval; O(n) time and O(n) space. Inputs are preserved.

function solve(edges) {
  const visited = Array(edges.length).fill(0);
  let clock = 1;
  let answer = -1;
  for (let start = 0; start < edges.length; start += 1) {
    if (visited[start] !== 0) continue;
    const beginning = clock;
    let node = start;
    while (node !== -1 && visited[node] === 0) {
      visited[node] = clock;
      clock += 1;
      node = edges[node];
    }
    if (node !== -1 && visited[node] >= beginning) answer = Math.max(answer, clock - visited[node]);
  }
  return answer;
}

const longestCycle = solve;
class Solution {
  longestCycle(edges) { return solve(edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestCycle };
