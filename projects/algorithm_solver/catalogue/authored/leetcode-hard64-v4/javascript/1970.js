'use strict';

// 1970. Last Day Where You Can Still Cross. Reverse flooding with union-find and virtual borders; O(R*C*alpha(R*C)) time, O(R*C) space. Inputs are preserved.

class DisjointSet {
  constructor(size) {
    this.parent = Array.from({ length: size }, (_, index) => index);
    this.sizes = Array(size).fill(1);
  }
  find(node) {
    while (node !== this.parent[node]) {
      this.parent[node] = this.parent[this.parent[node]];
      node = this.parent[node];
    }
    return node;
  }
  union(left, right) {
    let a = this.find(left);
    let b = this.find(right);
    if (a === b) return;
    if (this.sizes[a] < this.sizes[b]) [a, b] = [b, a];
    this.parent[b] = a;
    this.sizes[a] += this.sizes[b];
  }
}

function solve(row, col, cells) {
  const count = row * col;
  const sets = new DisjointSet(count + 2);
  const land = new Uint8Array(count);
  const top = count;
  const bottom = count + 1;
  const directions = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  for (let day = cells.length - 1; day >= 0; day -= 1) {
    const r = cells[day][0] - 1;
    const c = cells[day][1] - 1;
    const cell = r * col + c;
    land[cell] = 1;
    if (r === 0) sets.union(cell, top);
    if (r === row - 1) sets.union(cell, bottom);
    for (const [dr, dc] of directions) {
      const nr = r + dr;
      const nc = c + dc;
      if (nr >= 0 && nr < row && nc >= 0 && nc < col && land[nr * col + nc]) {
        sets.union(cell, nr * col + nc);
      }
    }
    if (sets.find(top) === sets.find(bottom)) return day;
  }
  return 0;
}

const latestDayToCross = solve;
class Solution {
  latestDayToCross(row, col, cells) { return solve(row, col, cells); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, latestDayToCross };
