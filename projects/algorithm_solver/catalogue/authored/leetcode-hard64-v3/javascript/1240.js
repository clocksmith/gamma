'use strict';

// 1240. Tiling a Rectangle with the Fewest Squares: skyline branch-and-bound with reflected-state memoization; exponential worst-case search.

function solve(n, m) {
  const height = Math.max(n, m);
  const width = Math.min(n, m);
  const skyline = Array(width).fill(0);
  const seen = new Map();
  let best = height * width;
  function search(used) {
    if (used >= best) return;
    const level = Math.min(...skyline);
    if (level === height) {
      best = used;
      return;
    }
    const forward = skyline.join(',');
    const reverse = skyline.slice().reverse().join(',');
    const key = forward < reverse ? forward : reverse;
    if (seen.has(key) && seen.get(key) <= used) return;
    seen.set(key, used);
    const left = skyline.indexOf(level);
    let right = left;
    while (right < width && skyline[right] === level) right += 1;
    const maximum = Math.min(right - left, height - level);
    for (let side = maximum; side > 0; side -= 1) {
      for (let column = left; column < left + side; column += 1) skyline[column] += side;
      search(used + 1);
      for (let column = left; column < left + side; column += 1) skyline[column] -= side;
    }
  }
  search(0);
  return best;
}

const tilingRectangle = solve;
class Solution {
  tilingRectangle(n, m) { return solve(n, m); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, tilingRectangle };
