'use strict';

// 407. Trapping Rain Water II. Flood inward from the lowest boundary; preserves the height map.

class _Heap {
  constructor(less = (a, b) => a < b) { this.data = []; this.less = less; }
  get size() { return this.data.length; }
  peek() { return this.data[0]; }
  push(value) {
    const a = this.data;
    let i = a.length;
    a.push(value);
    while (i > 0) {
      const parent = Math.floor((i - 1) / 2);
      if (!this.less(value, a[parent])) break;
      a[i] = a[parent];
      i = parent;
    }
    a[i] = value;
  }
  pop() {
    const a = this.data;
    if (a.length === 0) return undefined;
    const result = a[0];
    const last = a.pop();
    if (a.length > 0) {
      let i = 0;
      while (2 * i + 1 < a.length) {
        let child = 2 * i + 1;
        if (child + 1 < a.length && this.less(a[child + 1], a[child])) child += 1;
        if (!this.less(a[child], last)) break;
        a[i] = a[child];
        i = child;
      }
      a[i] = last;
    }
    return result;
  }
}

function solve(heightMap) {
  const rows = heightMap.length, cols = heightMap[0].length;
  if (rows < 3 || cols < 3) return 0;
  const seen = Array.from({length: rows}, () => Array(cols).fill(false));
  const heap = new _Heap((a, b) => a[0] < b[0]);
  for (let r = 0; r < rows; r += 1) {
    for (let c = 0; c < cols; c += 1) {
      if (r === 0 || r === rows - 1 || c === 0 || c === cols - 1) {
        seen[r][c] = true; heap.push([heightMap[r][c], r, c]);
      }
    }
  }
  let answer = 0;
  while (heap.size > 0) {
    const [level, row, col] = heap.pop();
    for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const nr = row + dr, nc = col + dc;
      if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && !seen[nr][nc]) {
        seen[nr][nc] = true;
        const height = heightMap[nr][nc];
        answer += Math.max(0, level - height);
        heap.push([Math.max(level, height), nr, nc]);
      }
    }
  }
  return answer;
}

const trapRainWater = solve;
class Solution {
  trapRainWater(heightMap) { return solve(heightMap); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, trapRainWater };
