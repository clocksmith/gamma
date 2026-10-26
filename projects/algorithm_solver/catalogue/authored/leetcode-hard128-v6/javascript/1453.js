'use strict';

// 1453. Maximum Number of Darts Inside of a Circular Dartboard.
// Enumerate circle centers fixed by two boundary points; O(n^3) time, O(1) auxiliary space. Inputs are preserved.

function solve(darts, r) {
  const radiusSquared = r * r;
  function count(x, y) {
    let result = 0;
    for (const [a, b] of darts) if ((a - x) ** 2 + (b - y) ** 2 <= radiusSquared + 1e-7) result += 1;
    return result;
  }
  let answer = 0;
  for (const [x, y] of darts) answer = Math.max(answer, count(x, y));
  for (let i = 0; i < darts.length; i += 1) {
    const [x1, y1] = darts[i];
    for (let j = i + 1; j < darts.length; j += 1) {
      const [x2, y2] = darts[j];
      const dx = x2 - x1, dy = y2 - y1;
      const distanceSquared = dx * dx + dy * dy;
      if (distanceSquared === 0 || distanceSquared > 4 * radiusSquared) continue;
      const scale = Math.sqrt(Math.max(0, radiusSquared / distanceSquared - 0.25));
      const middleX = (x1 + x2) / 2, middleY = (y1 + y2) / 2;
      answer = Math.max(answer, count(middleX - dy * scale, middleY + dx * scale), count(middleX + dy * scale, middleY - dx * scale));
    }
  }
  return answer;
}

const numPoints = solve;
class Solution {
  numPoints(darts, r) { return solve(darts, r); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numPoints };
