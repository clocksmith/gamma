'use strict';

// 2392. Build a Matrix With Conditions: independent topological coordinates.
// O(k^2 + E) time and space, including the returned matrix. Inputs are preserved.
function solve(k, rowConditions, colConditions) {
  function order(conditions) {
    const adjacency = Array.from({ length: k + 1 }, () => []);
    const degree = new Int32Array(k + 1);
    for (const [first, second] of conditions) {
      adjacency[first].push(second);
      degree[second] += 1;
    }
    const result = [];
    for (let value = 1; value <= k; value += 1) {
      if (degree[value] === 0) result.push(value);
    }
    for (let head = 0; head < result.length; head += 1) {
      for (const following of adjacency[result[head]]) {
        degree[following] -= 1;
        if (degree[following] === 0) result.push(following);
      }
    }
    return result;
  }
  const rows = order(rowConditions);
  const columns = order(colConditions);
  if (rows.length !== k || columns.length !== k) return [];
  const columnPosition = new Int32Array(k + 1);
  for (let position = 0; position < k; position += 1) columnPosition[columns[position]] = position;
  const answer = Array.from({ length: k }, () => Array(k).fill(0));
  for (let position = 0; position < k; position += 1) {
    const value = rows[position];
    answer[position][columnPosition[value]] = value;
  }
  return answer;
}

const buildMatrix = solve;
class Solution {
  buildMatrix(k, rowConditions, colConditions) { return solve(k, rowConditions, colConditions); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, buildMatrix };
