'use strict';

// 3283. Maximum Number of Moves to Kill All Pawns: knight-distance searches followed by subset minimax.
// O(n*2500 + n^2*2^n) time and O(2500 + n*2^n) auxiliary space. Inputs are preserved.
function solve(kx, ky, positions) {
  const n = positions.length;
  const locations = [...positions, [kx, ky]];
  const directions = [[1, 2], [2, 1], [-1, 2], [-2, 1], [1, -2], [2, -1], [-1, -2], [-2, -1]];
  const distance = [];
  for (const [startX, startY] of locations) {
    const seen = new Int32Array(2500).fill(-1);
    const queue = new Int32Array(2500);
    const start = startX * 50 + startY;
    seen[start] = 0;
    queue[0] = start;
    let head = 0;
    let tail = 1;
    while (head < tail) {
      const cell = queue[head++];
      const x = Math.floor(cell / 50);
      const y = cell % 50;
      for (const [dx, dy] of directions) {
        const nx = x + dx;
        const ny = y + dy;
        if (nx < 0 || nx >= 50 || ny < 0 || ny >= 50) continue;
        const following = nx * 50 + ny;
        if (seen[following] !== -1) continue;
        seen[following] = seen[cell] + 1;
        queue[tail++] = following;
      }
    }
    distance.push(positions.map(([x, y]) => seen[x * 50 + y]));
  }
  const size = 1 << n;
  const bits = new Uint8Array(size);
  for (let mask = 1; mask < size; mask += 1) bits[mask] = bits[mask >> 1] + (mask & 1);
  const memo = new Int32Array(size * (n + 1)).fill(-1);
  function visit(mask, last) {
    if (mask === 0) return 0;
    const key = mask * (n + 1) + last;
    if (memo[key] >= 0) return memo[key];
    const maximizing = (n - bits[mask]) % 2 === 0;
    let value = maximizing ? -1 : 1000000;
    let remaining = mask;
    while (remaining !== 0) {
      const bit = remaining & -remaining;
      remaining -= bit;
      const following = 31 - Math.clz32(bit);
      const candidate = distance[last][following] + visit(mask ^ bit, following);
      value = maximizing ? Math.max(value, candidate) : Math.min(value, candidate);
    }
    memo[key] = value;
    return value;
  }
  return visit(size - 1, n);
}

const maxMoves = solve;
class Solution {
  maxMoves(kx, ky, positions) { return solve(kx, ky, positions); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxMoves };
