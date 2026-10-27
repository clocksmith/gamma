'use strict';

// 699. Falling Squares. Compressed half-open coordinates and a range-maximum/range-assignment tree.

function solve(positions) {
  if (positions.length === 0) return [];
  const endpoints = new Set();
  for (const [left, size] of positions) { endpoints.add(left); endpoints.add(left + size); }
  const coordinates = Array.from(endpoints).sort((a, b) => a - b), rank = new Map(coordinates.map((value, i) => [value, i]));
  const n = coordinates.length - 1, maximum = Array(4 * n + 4).fill(0), lazy = Array(4 * n + 4).fill(null);
  function push(node) {
    if (lazy[node] !== null) {
      maximum[2 * node] = maximum[2 * node + 1] = lazy[node];
      lazy[2 * node] = lazy[2 * node + 1] = lazy[node]; lazy[node] = null;
    }
  }
  function query(node, low, high, left, right) {
    if (left <= low && high <= right) return maximum[node];
    push(node);
    const middle = Math.floor((low + high) / 2);
    let result = 0;
    if (left <= middle) result = query(2 * node, low, middle, left, right);
    if (right > middle) result = Math.max(result, query(2 * node + 1, middle + 1, high, left, right));
    return result;
  }
  function assign(node, low, high, left, right, value) {
    if (left <= low && high <= right) { maximum[node] = lazy[node] = value; return; }
    push(node);
    const middle = Math.floor((low + high) / 2);
    if (left <= middle) assign(2 * node, low, middle, left, right, value);
    if (right > middle) assign(2 * node + 1, middle + 1, high, left, right, value);
    maximum[node] = Math.max(maximum[2 * node], maximum[2 * node + 1]);
  }
  const answer = [];
  for (const [left, size] of positions) {
    const a = rank.get(left), b = rank.get(left + size) - 1, height = query(1, 0, n - 1, a, b) + size;
    assign(1, 0, n - 1, a, b, height); answer.push(maximum[1]);
  }
  return answer;
}

const fallingSquares = solve;
class Solution {
  fallingSquares(positions) { return solve(positions); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, fallingSquares };
