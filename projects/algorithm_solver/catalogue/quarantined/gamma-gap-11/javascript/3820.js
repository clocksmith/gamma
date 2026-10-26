'use strict';

// 3820. Pythagorean Distance Nodes in a Tree.
// O(n) time and space; three iterative traversals, including valid zero-distance triples.
function solve(n, edges, x, y, z) {
  const graph = Array.from({ length: n }, () => []);
  for (const [left, right] of edges) {
    graph[left].push(right);
    graph[right].push(left);
  }
  function distances(origin) {
    const result = Array(n).fill(-1);
    const queue = [origin];
    result[origin] = 0;
    for (let cursor = 0; cursor < queue.length; cursor += 1) {
      const node = queue[cursor];
      for (const child of graph[node]) {
        if (result[child] < 0) {
          result[child] = result[node] + 1;
          queue.push(child);
        }
      }
    }
    return result;
  }
  const rows = [distances(x), distances(y), distances(z)];
  let answer = 0;
  for (let index = 0; index < n; index += 1) {
    const values = rows.map(row => row[index]).sort((left, right) => left - right);
    if (values[0] ** 2 + values[1] ** 2 === values[2] ** 2) answer += 1;
  }
  return answer;
}

const specialNodes = solve;
class Solution {
  specialNodes(n, edges, x, y, z) { return solve(n, edges, x, y, z); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, specialNodes };
