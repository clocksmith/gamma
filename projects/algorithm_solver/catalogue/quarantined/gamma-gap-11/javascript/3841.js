'use strict';

// 3841. Palindromic Path Queries in a Tree.
// O((n+q) log n) time and O(n log n) space; Euler subtree XOR updates plus binary-lifting LCA.
function solve(n, edges, s, queries) {
  const graph = Array.from({ length: n }, () => []);
  for (const [left, right] of edges) {
    graph[left].push(right);
    graph[right].push(left);
  }
  const parent = Array(n).fill(0);
  const depth = Array(n).fill(0);
  const entry = Array(n).fill(0);
  const exitTime = Array(n).fill(0);
  const letters = Array.from(s, char => 1 << (char.charCodeAt(0) - 97));
  const original = Array(n).fill(0);
  let clock = 0;
  const stack = [[0, 0, false]];
  while (stack.length > 0) {
    const [node, ancestor, leaving] = stack.pop();
    if (leaving) {
      exitTime[node] = clock;
      continue;
    }
    parent[node] = ancestor;
    entry[node] = clock;
    clock += 1;
    original[node] = letters[node] ^ (node === 0 ? 0 : original[ancestor]);
    stack.push([node, ancestor, true]);
    for (const child of graph[node]) {
      if (child !== ancestor) {
        depth[child] = depth[node] + 1;
        stack.push([child, node, false]);
      }
    }
  }
  const levels = [parent];
  for (let scale = 2; scale <= n; scale *= 2) {
    const before = levels[levels.length - 1];
    levels.push(Array.from({ length: n }, (_, node) => before[before[node]]));
  }
  function lca(left, right) {
    if (depth[left] < depth[right]) [left, right] = [right, left];
    const difference = depth[left] - depth[right];
    for (let bit = 0; bit < levels.length; bit += 1) if (difference & (1 << bit)) left = levels[bit][left];
    if (left === right) return left;
    for (let bit = levels.length - 1; bit >= 0; bit -= 1) {
      if (levels[bit][left] !== levels[bit][right]) {
        left = levels[bit][left];
        right = levels[bit][right];
      }
    }
    return parent[left];
  }
  const fenwick = new Int32Array(n + 1);
  function toggle(index, value) {
    for (index += 1; index <= n; index += index & -index) fenwick[index] ^= value;
  }
  function prefix(node) {
    let value = original[node];
    for (let index = entry[node] + 1; index > 0; index -= index & -index) value ^= fenwick[index];
    return value;
  }
  const answer = [];
  for (const command of queries) {
    const [operation, first, second] = command.split(' ');
    const node = Number(first);
    if (operation === 'update') {
      const value = 1 << (second.charCodeAt(0) - 97);
      const delta = letters[node] ^ value;
      letters[node] = value;
      toggle(entry[node], delta);
      toggle(exitTime[node], delta);
    } else {
      const other = Number(second);
      const parity = prefix(node) ^ prefix(other) ^ letters[lca(node, other)];
      answer.push((parity & (parity - 1)) === 0);
    }
  }
  return answer;
}

const palindromePath = solve;
class Solution {
  palindromePath(n, edges, s, queries) { return solve(n, edges, s, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, palindromePath };
