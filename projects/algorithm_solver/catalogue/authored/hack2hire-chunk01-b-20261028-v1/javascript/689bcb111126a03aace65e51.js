"use strict";
// Hack2Hire 689bcb111126a03aace65e51 (Find Closest Dashmart). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

function solve(city, locations) {
  const rows = city.length, cols = city[0].length;
  const dist = new Array(rows * cols).fill(-1), frontier = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (city[r][c] === "D") {
        dist[r * cols + c] = 0;
        frontier.push(r * cols + c);
      }
    }
  }
  const moves = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  for (let head = 0; head < frontier.length; head++) {
    const cell = frontier[head], r = Math.floor(cell / cols), c = cell % cols;
    for (const [dr, dc] of moves) {
      const x = r + dr, y = c + dc;
      if (x >= 0 && x < rows && y >= 0 && y < cols && dist[x * cols + y] < 0 && city[x][y] !== "X") {
        dist[x * cols + y] = dist[cell] + 1;
        frontier.push(x * cols + y);
      }
    }
  }
  return locations.map(([r, c]) => dist[r * cols + c]);
}

function closestDashmartDistances(city, locations) { return solve(city, locations); }
module.exports = solve;
module.exports.closestDashmartDistances = closestDashmartDistances;
