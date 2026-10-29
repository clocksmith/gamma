// Original hack2hire:689bf3a41126a03aace65e63; inferred public-preview contract; qualification unknown.
"use strict";
function countFullyCoveredClusters(availability, users) {
  if (!users.length) return 0;
  const rows = users.length, cols = users[0].length, seen = new Set();
  let result = 0;
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const id = r * cols + c;
    if (!users[r][c] || seen.has(id)) continue;
    const queue = [[r, c]]; seen.add(id);
    let covered = true;
    for (let head = 0; head < queue.length; head++) {
      const [x, y] = queue[head];
      if (!availability[x][y]) covered = false;
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const a = x + dx, b = y + dy, next = a * cols + b;
        if (a >= 0 && a < rows && b >= 0 && b < cols && users[a][b] && !seen.has(next)) {
          seen.add(next); queue.push([a, b]);
        }
      }
    }
    if (covered) result++;
  }
  return result;
}

const solve = countFullyCoveredClusters;
module.exports = solve;
module.exports.countFullyCoveredClusters = countFullyCoveredClusters;
module.exports.Solution = class { countFullyCoveredClusters(...args) { return countFullyCoveredClusters(...args); } };
