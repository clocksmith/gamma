'use strict';
// 305. Number of Islands II.
function solve(m, n, positions) {
  const parent = new Map(); const size = new Map(); const result = []; let count = 0;
  function find(node) {
    let current = node;
    while (parent.get(current) !== current) {
      parent.set(current, parent.get(parent.get(current)));
      current = parent.get(current);
    }
    return current;
  }
  for (const [row, column] of positions) {
    const node = row * n + column;
    if (parent.has(node)) { result.push(count); continue; }
    parent.set(node, node); size.set(node, 1); count += 1;
    for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const nr = row + dr; const nc = column + dc; const neighbor = nr * n + nc;
      if (nr < 0 || nr >= m || nc < 0 || nc >= n || !parent.has(neighbor)) continue;
      let root = find(node); let other = find(neighbor);
      if (root !== other) {
        if (size.get(root) < size.get(other)) [root, other] = [other, root];
        parent.set(other, root); size.set(root, size.get(root) + size.get(other)); count -= 1;
      }
    }
    result.push(count);
  }
  return result;
}
const numIslands2 = solve;
class Solution { numIslands2(m, n, positions) { return solve(m, n, positions); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numIslands2 };
