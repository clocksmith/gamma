'use strict';

// 1284. Minimum Number of Flips to Convert Binary Matrix to Zero Matrix: bitmask BFS for at most nine cells; O(cells*2^cells) time and O(2^cells) space.

function solve(mat) {
  const rows = mat.length;
  const columns = mat[0].length;
  let start = 0;
  const flips = [];
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      start |= mat[row][column] << (row * columns + column);
      let mask = 0;
      for (const [dr, dc] of [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nr = row + dr;
        const nc = column + dc;
        if (nr >= 0 && nr < rows && nc >= 0 && nc < columns) mask |= 1 << (nr * columns + nc);
      }
      flips.push(mask);
    }
  }
  const queue = [[start, 0]];
  const seen = new Set([start]);
  for (let head = 0; head < queue.length; head += 1) {
    const [state, distance] = queue[head];
    if (state === 0) return distance;
    for (const mask of flips) {
      const following = state ^ mask;
      if (!seen.has(following)) {
        seen.add(following);
        queue.push([following, distance + 1]);
      }
    }
  }
  return -1;
}

const minFlips = solve;
class Solution {
  minFlips(mat) { return solve(mat); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minFlips };
