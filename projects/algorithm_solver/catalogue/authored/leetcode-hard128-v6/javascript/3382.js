'use strict';

// 3382. Maximum Area Rectangle With Point Constraints II.
// Sweep columns, pair adjacent heights, and query the latest intervening x-coordinate; O(n log n) time and O(n) space. Areas fit exactly below 2^53. Inputs are preserved.

function solve(xCoord, yCoord) {
  const points = xCoord.map((x, index) => [x, yCoord[index]]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const heights = [...new Set(yCoord)].sort((a, b) => a - b), rank = new Map(heights.map((value, index) => [value, index]));
  let size = 1;
  while (size < heights.length) size *= 2;
  const latest = new Float64Array(2 * size).fill(-1);
  function update(index, value) {
    index += size; latest[index] = value;
    for (index = Math.floor(index / 2); index > 0; index = Math.floor(index / 2)) latest[index] = Math.max(latest[2 * index], latest[2 * index + 1]);
  }
  function maximum(left, right) {
    left += size; right += size + 1;
    let answer = -1;
    while (left < right) {
      if (left % 2) { answer = Math.max(answer, latest[left]); left += 1; }
      if (right % 2) { right -= 1; answer = Math.max(answer, latest[right]); }
      left = Math.floor(left / 2); right = Math.floor(right / 2);
    }
    return answer;
  }
  const previous = new Map();
  let answer = -1, start = 0;
  while (start < points.length) {
    let end = start + 1;
    const x = points[start][0];
    while (end < points.length && points[end][0] === x) end += 1;
    for (let index = start + 1; index < end; index += 1) {
      const bottom = points[index - 1][1], top = points[index][1], pair = bottom + ',' + top;
      const old = previous.get(pair);
      if (old !== undefined && maximum(rank.get(bottom), rank.get(top)) === old) answer = Math.max(answer, (x - old) * (top - bottom));
      previous.set(pair, x);
    }
    for (let index = start; index < end; index += 1) update(rank.get(points[index][1]), x);
    start = end;
  }
  return answer;
}

const maxRectangleArea = solve;
class Solution {
  maxRectangleArea(xCoord, yCoord) { return solve(xCoord, yCoord); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxRectangleArea };
