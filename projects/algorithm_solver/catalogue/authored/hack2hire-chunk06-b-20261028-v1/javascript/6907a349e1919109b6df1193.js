"use strict";
// Hack2Hire 6907a349e1919109b6df1193 (Knight Paths on a Phone Keypad) over an INFERRED spec; qualification unknown.

const POSITION = [[3, 1], [0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2]];
const MOVES = POSITION.map(([r, c]) => {
  const out = [];
  for (let b = 0; b < 10; b++) {
    const dr = Math.abs(POSITION[b][0] - r), dc = Math.abs(POSITION[b][1] - c);
    if ((dr === 1 && dc === 2) || (dr === 2 && dc === 1)) out.push(b);
  }
  return out;
});

function solve(start, end) {
  const dist = new Array(10).fill(-1);
  dist[start] = 0;
  let frontier = [start];
  while (frontier.length) {
    const next = [];
    for (const a of frontier) for (const b of MOVES[a]) if (dist[b] < 0) { dist[b] = dist[a] + 1; next.push(b); }
    frontier = next;
  }
  if (dist[end] < 0) return [];
  const paths = [], stack = [[start, String(start)]];
  while (stack.length) {
    const [a, path] = stack.pop();
    if (a === end) { paths.push(path); continue; }
    for (const b of MOVES[a]) if (dist[b] === dist[a] + 1 && dist[b] <= dist[end]) stack.push([b, path + b]);
  }
  return paths.sort();
}

function knightPaths(start, end) { return solve(start, end); }

module.exports = solve;
module.exports.knightPaths = knightPaths;
