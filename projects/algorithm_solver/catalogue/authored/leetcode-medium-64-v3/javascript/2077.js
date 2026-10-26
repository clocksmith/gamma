'use strict';

// 2077. Paths in Maze That Lead to Same Room: count triangles once using degree-ordered forward edges.
// O(n + e * sqrt(e)) expected time and O(n + e) auxiliary space; inputs are read-only.
function solve(n, corridors) {
  const degree = new Int32Array(n);
  for (const [left, right] of corridors) {
    degree[left - 1] += 1;
    degree[right - 1] += 1;
  }
  const forward = Array.from({ length: n }, () => new Set());
  for (const edge of corridors) {
    let left = edge[0] - 1;
    let right = edge[1] - 1;
    if (degree[left] > degree[right] || (degree[left] === degree[right] && left > right)) [left, right] = [right, left];
    forward[left].add(right);
  }
  let answer = 0;
  for (let first = 0; first < n; first += 1) {
    for (const second of forward[first]) {
      for (const third of forward[second]) {
        if (forward[first].has(third)) answer += 1;
      }
    }
  }
  return answer;
}

const numberOfPaths = solve;
class Solution {
  numberOfPaths(n, corridors) { return solve(n, corridors); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfPaths };
