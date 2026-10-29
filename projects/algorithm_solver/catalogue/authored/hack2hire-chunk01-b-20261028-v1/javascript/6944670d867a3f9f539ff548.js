"use strict";
// Hack2Hire 6944670d867a3f9f539ff548 (Find Optimal Commute, variant 2: mode switching). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

class MinHeap {
  constructor(less) {
    this.items = [];
    this.less = less;
  }
  get size() { return this.items.length; }
  peek() { return this.items[0]; }
  push(item) {
    const a = this.items;
    a.push(item);
    let i = a.length - 1;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (!this.less(a[i], a[p])) break;
      [a[i], a[p]] = [a[p], a[i]];
      i = p;
    }
  }
  pop() {
    const a = this.items, top = a[0], last = a.pop();
    if (a.length) {
      a[0] = last;
      let i = 0;
      for (;;) {
        const l = 2 * i + 1, r = l + 1;
        let m = i;
        if (l < a.length && this.less(a[l], a[m])) m = l;
        if (r < a.length && this.less(a[r], a[m])) m = r;
        if (m === i) break;
        [a[i], a[m]] = [a[m], a[i]];
        i = m;
      }
    }
    return top;
  }
}

function solve(grid, modes, times, costs) {
  const rows = grid.length, cols = grid[0].length;
  let start = -1;
  for (let r = 0; r < rows && start < 0; r++) {
    const c = grid[r].indexOf("S");
    if (c >= 0) start = r * cols + c;
  }
  const bestTime = new Array(rows * cols).fill(-1), bestCost = new Array(rows * cols).fill(-1);
  const less = (x, y) => x[0] < y[0] || (x[0] === y[0] && x[1] < y[1]);
  const heap = new MinHeap(less);
  bestTime[start] = 0;
  bestCost[start] = 0;
  heap.push([0, 0, start]);
  const moves = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  while (heap.size) {
    const [time, cost, cell] = heap.pop();
    if (bestTime[cell] !== time || bestCost[cell] !== cost) continue;
    const r = Math.floor(cell / cols), c = cell % cols, ch = grid[r][c];
    if (ch === "D") return [time, cost];
    const stepTime = ch === "S" ? 0 : times[Number(ch) - 1], stepCost = ch === "S" ? 0 : costs[Number(ch) - 1];
    const candidate = [time + stepTime, cost + stepCost];
    for (const [dr, dc] of moves) {
      const x = r + dr, y = c + dc;
      if (x < 0 || x >= rows || y < 0 || y >= cols || grid[x][y] === "X" || grid[x][y] === "S") continue;
      const next = x * cols + y;
      if (bestTime[next] < 0 || less(candidate, [bestTime[next], bestCost[next]])) {
        bestTime[next] = candidate[0];
        bestCost[next] = candidate[1];
        heap.push([candidate[0], candidate[1], next]);
      }
    }
  }
  return [-1, -1];
}

function optimalCommuteCost(grid, modes, times, costs) { return solve(grid, modes, times, costs); }
module.exports = solve;
module.exports.optimalCommuteCost = optimalCommuteCost;
