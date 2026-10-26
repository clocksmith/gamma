'use strict';

// 2581. Count Number of Possible Root Nodes. Reroot the number of correct directed parent guesses; O(n+g) expected time and O(n+g) space. Inputs are preserved.

function solve(edges, guesses, k) {
  const size = edges.length + 1;
  const graph = Array.from({ length: size }, () => []);
  for (const [first, second] of edges) {
    graph[first].push(second);
    graph[second].push(first);
  }
  const guessed = new Set(guesses.map(([first, second]) => first * size + second));
  const parent = Array(size).fill(-1);
  const order = [0];
  for (let index = 0; index < order.length; index += 1) {
    const node = order[index];
    for (const neighbor of graph[node]) {
      if (neighbor === parent[node]) continue;
      parent[neighbor] = node;
      order.push(neighbor);
    }
  }
  const score = Array(size).fill(0);
  for (let index = 1; index < size; index += 1) {
    const node = order[index];
    if (guessed.has(parent[node] * size + node)) score[0] += 1;
  }
  for (let index = 1; index < size; index += 1) {
    const node = order[index];
    const previous = parent[node];
    score[node] = score[previous] - Number(guessed.has(previous * size + node)) + Number(guessed.has(node * size + previous));
  }
  let answer = 0;
  for (const value of score) if (value >= k) answer += 1;
  return answer;
}

const rootCount = solve;
class Solution {
  rootCount(edges, guesses, k) { return solve(edges, guesses, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, rootCount };
