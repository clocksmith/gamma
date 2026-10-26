'use strict';

// 3311. Construct 2D Grid Matching Graph Layout: derive grid coordinates from distances to adjacent corners.
// O(n + E) time and O(n + E) space under the rectangular-grid promise. Inputs are preserved.
function solve(n, edges) {
  if (n === 1) return [[0]];
  const graph = Array.from({ length: n }, () => []);
  for (const [first, second] of edges) {
    graph[first].push(second);
    graph[second].push(first);
  }
  let corner = 0;
  for (let node = 1; node < n; node += 1) {
    if (graph[node].length < graph[corner].length) corner = node;
  }
  function distances(start) {
    const distance = new Int32Array(n).fill(-1);
    const queue = new Int32Array(n);
    let tail = 1;
    queue[0] = start;
    distance[start] = 0;
    for (let head = 0; head < tail; head += 1) {
      const node = queue[head];
      for (const neighbor of graph[node]) {
        if (distance[neighbor] === -1) {
          distance[neighbor] = distance[node] + 1;
          queue[tail++] = neighbor;
        }
      }
    }
    return distance;
  }
  const firstDistance = distances(corner);
  if (graph[corner].length === 1) {
    const row = new Array(n);
    for (let node = 0; node < n; node += 1) row[firstDistance[node]] = node;
    return [row];
  }
  let other = -1;
  for (let node = 0; node < n; node += 1) {
    if (node === corner || graph[node].length !== 2) continue;
    if (other === -1 || firstDistance[node] < firstDistance[other]) other = node;
  }
  const secondDistance = distances(other);
  const width = firstDistance[other] + 1;
  const height = n / width;
  const answer = Array.from({ length: height }, () => new Array(width).fill(0));
  for (let node = 0; node < n; node += 1) {
    const row = (firstDistance[node] + secondDistance[node] - width + 1) / 2;
    const column = (firstDistance[node] - secondDistance[node] + width - 1) / 2;
    answer[row][column] = node;
  }
  return answer;
}

const constructGridLayout = solve;
class Solution {
  constructGridLayout(n, edges) { return solve(n, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, constructGridLayout };
