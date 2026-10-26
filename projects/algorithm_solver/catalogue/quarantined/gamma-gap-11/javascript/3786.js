'use strict';

// 3786. Total Sum of Interaction Cost in Tree Groups.
// O(20n) time and O(n) auxiliary space; charge each edge once for every same-group pair crossing it.
function solve(n, edges, group) {
  const graph = Array.from({ length: n }, () => []);
  for (const [left, right] of edges) {
    graph[left].push(right);
    graph[right].push(left);
  }
  const parent = new Int32Array(n).fill(-1);
  const order = [0];
  for (let head = 0; head < order.length; head += 1) {
    const node = order[head];
    for (const child of graph[node]) {
      if (child !== parent[node]) {
        parent[child] = node;
        order.push(child);
      }
    }
  }
  let answer = 0;
  for (const label of new Set(group)) {
    const count = new Int32Array(n);
    let total = 0;
    for (let index = 0; index < n; index += 1) {
      if (group[index] === label) {
        count[index] = 1;
        total += 1;
      }
    }
    for (let index = n - 1; index > 0; index -= 1) {
      const node = order[index];
      const amount = count[node];
      answer += amount * (total - amount);
      count[parent[node]] += amount;
    }
  }
  return answer;
}

const interactionCosts = solve;
class Solution {
  interactionCosts(n, edges, group) { return solve(n, edges, group); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, interactionCosts };
