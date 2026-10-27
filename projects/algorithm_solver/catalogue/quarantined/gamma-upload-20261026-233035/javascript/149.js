'use strict';
// 149. Max Points on a Line.
function gcd(a, b) { a = Math.abs(a); b = Math.abs(b); while (b) [a, b] = [b, a % b]; return a; }
function solve(points) {
  if (points.length <= 2) return points.length;
  let best = 0;
  for (let index = 0; index < points.length; index += 1) {
    const slopes = new Map();
    let duplicates = 1; let local = 0;
    for (let other = index + 1; other < points.length; other += 1) {
      let dx = points[other][0] - points[index][0];
      let dy = points[other][1] - points[index][1];
      if (dx === 0 && dy === 0) { duplicates += 1; continue; }
      const divisor = gcd(dx, dy); dx /= divisor; dy /= divisor;
      if (dx < 0 || (dx === 0 && dy < 0)) { dx = -dx; dy = -dy; }
      const key = `${dy}:${dx}`;
      slopes.set(key, (slopes.get(key) || 0) + 1);
      local = Math.max(local, slopes.get(key));
    }
    best = Math.max(best, local + duplicates);
  }
  return best;
}
const maxPoints = solve;
class Solution { maxPoints(points) { return solve(points); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxPoints };
