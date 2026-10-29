// Original hack2hire:67eaec184c9bb801bfd0ef4d; inferred public-preview contract; qualification unknown.
"use strict";
function dualCarDestinations(grid) {
  const rows = grid.length, cols = grid[0].length, size = rows*cols, positions = {}, neighbors = new Map();
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const value = grid[r][c], cell = r*cols+c; if (value === '#') continue;
    if ('abAB'.includes(value)) positions[value] = cell;
    const next = [];
    for (const [dx,dy] of [[0,0],[1,0],[-1,0],[0,1],[0,-1]]) { const a = r+dx, b = c+dy; if (a >= 0 && a < rows && b >= 0 && b < cols && grid[a][b] !== '#') next.push(a*cols+b); }
    neighbors.set(cell,next);
  }
  const queue = [[positions.a,positions.b,0]], seen = new Set([positions.a*size+positions.b]);
  for (let head = 0; head < queue.length; head++) {
    const [a,b,distance] = queue[head]; if (a === positions.A && b === positions.B) return distance;
    for (const x of neighbors.get(a)) for (const y of neighbors.get(b)) {
      const id = x*size+y;
      if (x === y || x === b && y === a || seen.has(id)) continue;
      seen.add(id); queue.push([x,y,distance+1]);
    }
  }
  return -1;
}

const solve = dualCarDestinations;
module.exports = solve;
module.exports.dualCarDestinations = dualCarDestinations;
module.exports.Solution = class { dualCarDestinations(...args) { return dualCarDestinations(...args); } };
