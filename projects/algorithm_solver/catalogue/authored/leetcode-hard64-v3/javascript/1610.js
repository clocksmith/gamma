'use strict';

// 1610. Maximum Number of Visible Points: sorted polar-angle sliding window; O(n log n) time and O(n) space.

function solve(points, angle, location) {
  if (angle >= 360) return points.length;
  const [originX, originY] = location;
  let coincident = 0;
  const directions = [];
  for (const [x, y] of points) {
    if (x === originX && y === originY) coincident += 1;
    else directions.push(Math.atan2(y - originY, x - originX) * 180 / Math.PI);
  }
  directions.sort((a, b) => a - b);
  const size = directions.length;
  const extended = directions.concat(directions.map(value => value + 360));
  let left = 0;
  let answer = 0;
  for (let right = 0; right < extended.length; right += 1) {
    while (right - left >= size || extended[right] - extended[left] > angle + 1e-10) left += 1;
    answer = Math.max(answer, right - left + 1);
  }
  return answer + coincident;
}

const visiblePoints = solve;
class Solution {
  visiblePoints(points, angle, location) { return solve(points, angle, location); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, visiblePoints };
