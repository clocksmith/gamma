'use strict';

// 1632. Rank Transform of a Matrix: equal-value row/column DSUs with deferred rank updates; O(V log V) time and O(V) space, V=rows*columns.

function solve(matrix) {
  const rows = matrix.length;
  const columns = matrix[0].length;
  const cells = [];
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) cells.push([matrix[row][column], row, column]);
  }
  cells.sort((a, b) => a[0] - b[0]);
  const rowRank = Array(rows).fill(0);
  const columnRank = Array(columns).fill(0);
  const answer = Array.from({ length: rows }, () => Array(columns).fill(0));
  let start = 0;
  while (start < cells.length) {
    let end = start + 1;
    while (end < cells.length && cells[end][0] === cells[start][0]) end += 1;
    const parent = new Map();
    const weight = new Map();
    function find(node) {
      if (!parent.has(node)) { parent.set(node, node); weight.set(node, 1); }
      while (parent.get(node) !== node) {
        parent.set(node, parent.get(parent.get(node)));
        node = parent.get(node);
      }
      return node;
    }
    for (let index = start; index < end; index += 1) {
      const [, row, column] = cells[index];
      let first = find(row);
      let second = find(rows + column);
      if (first !== second) {
        if (weight.get(first) < weight.get(second)) [first, second] = [second, first];
        parent.set(second, first);
        weight.set(first, weight.get(first) + weight.get(second));
      }
    }
    const required = new Map();
    for (let index = start; index < end; index += 1) {
      const [, row, column] = cells[index];
      const root = find(row);
      required.set(root, Math.max(required.get(root) || 0, rowRank[row] + 1, columnRank[column] + 1));
    }
    for (let index = start; index < end; index += 1) {
      const [, row, column] = cells[index];
      const rank = required.get(find(row));
      answer[row][column] = rank;
      rowRank[row] = Math.max(rowRank[row], rank);
      columnRank[column] = Math.max(columnRank[column], rank);
    }
    start = end;
  }
  return answer;
}

const matrixRankTransform = solve;
class Solution {
  matrixRankTransform(matrix) { return solve(matrix); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, matrixRankTransform };
