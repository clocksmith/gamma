// Original implementation. Contract: https://leetcode.com/problems/minimum-operations-to-remove-adjacent-ones-in-matrix/
"use strict";

function solve(grid) {
  const rows = grid.length;
  const columns = grid[0].length;
  const size = rows * columns;
  const left = [];
  const adjacency = new Map();
  for (let row = 0; row < rows; row++) {
    for (let column = 0; column < columns; column++) {
      if (!grid[row][column] || (row + column) % 2 !== 0) continue;
      const node = row * columns + column;
      left.push(node);
      const neighbors = [];
      for (const [x, y] of [[row - 1, column], [row + 1, column], [row, column - 1], [row, column + 1]]) {
        if (x >= 0 && x < rows && y >= 0 && y < columns && grid[x][y]) {
          neighbors.push(x * columns + y);
        }
      }
      adjacency.set(node, neighbors);
    }
  }
  // Minimum vertex cover in this bipartite grid equals maximum matching.
  const pairLeft = new Int32Array(size).fill(-1);
  const pairRight = new Int32Array(size).fill(-1);
  let matching = 0;
  while (true) {
    const distance = new Int32Array(size).fill(-1);
    const queue = [];
    for (const node of left) {
      if (pairLeft[node] < 0) {
        distance[node] = 0;
        queue.push(node);
      }
    }
    let shortest = size + 1;
    for (let index = 0; index < queue.length; index++) {
      const node = queue[index];
      if (distance[node] >= shortest) continue;
      for (const neighbor of adjacency.get(node)) {
        const paired = pairRight[neighbor];
        if (paired < 0) {
          shortest = Math.min(shortest, distance[node] + 1);
        } else if (distance[paired] < 0) {
          distance[paired] = distance[node] + 1;
          queue.push(paired);
        }
      }
    }
    if (shortest === size + 1) return matching;
    const nextEdge = new Int32Array(size);
    for (const start of left) {
      if (pairLeft[start] >= 0) continue;
      // Explicit layered DFS stack avoids dependence on the JS call-stack limit.
      let stack = [start];
      const rights = [];
      while (stack.length > 0) {
        const node = stack.at(-1);
        const neighbors = adjacency.get(node);
        let advanced = false;
        while (nextEdge[node] < neighbors.length) {
          const neighbor = neighbors[nextEdge[node]++];
          const paired = pairRight[neighbor];
          if (paired < 0 && distance[node] + 1 === shortest) {
            rights.push(neighbor);
            for (let index = 0; index < stack.length; index++) {
              pairLeft[stack[index]] = rights[index];
              pairRight[rights[index]] = stack[index];
            }
            matching++;
            stack = [];
            advanced = true;
            break;
          }
          if (paired >= 0 && distance[paired] === distance[node] + 1 && distance[paired] < shortest) {
            rights.push(neighbor);
            stack.push(paired);
            advanced = true;
            break;
          }
        }
        if (!advanced) {
          distance[node] = -1;
          stack.pop();
          if (rights.length > 0) rights.pop();
        }
      }
    }
  }
}

module.exports = solve;
