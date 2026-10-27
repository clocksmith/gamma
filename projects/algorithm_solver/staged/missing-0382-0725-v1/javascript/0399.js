'use strict';

// 399. Evaluate Division. Search a reciprocal weighted graph; inputs are preserved.

function solve(equations, values, queries) {
  const graph = new Map();
  function connect(a, b, value) {
    if (!graph.has(a)) graph.set(a, []);
    graph.get(a).push([b, value]);
  }
  for (let i = 0; i < equations.length; i += 1) {
    const [a, b] = equations[i];
    connect(a, b, values[i]); connect(b, a, 1 / values[i]);
  }
  return queries.map(([source, target]) => {
    if (!graph.has(source) || !graph.has(target)) return -1;
    const stack = [[source, 1]];
    const visited = new Set([source]);
    while (stack.length > 0) {
      const [node, product] = stack.pop();
      if (node === target) return product;
      for (const [neighbor, ratio] of graph.get(node)) {
        if (!visited.has(neighbor)) {
          visited.add(neighbor); stack.push([neighbor, product * ratio]);
        }
      }
    }
    return -1;
  });
}

const calcEquation = solve;
class Solution {
  calcEquation(equations, values, queries) { return solve(equations, values, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, calcEquation };
