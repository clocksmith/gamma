/* Original candidate for LeetCode 2613. Contract: https://leetcode.com/problems/beautiful-pairs/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log n) time by closest-pair packing, O(n log n) conservative transient space */
"use strict";

function solve(x, y) {
  const points = x.map((value, index) => [value, y[index], index]);
  points.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
  let distance = Infinity;
  let pair = [x.length, x.length];
  function consider(a, b) {
    const candidateDistance = Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]);
    const candidate = [Math.min(a[2], b[2]), Math.max(a[2], b[2])];
    const earlier = candidate[0] < pair[0] ||
      (candidate[0] === pair[0] && candidate[1] < pair[1]);
    if (candidateDistance < distance || (candidateDistance === distance && earlier)) {
      distance = candidateDistance;
      pair = candidate;
    }
  }
  // Coincident points need separate handling for the strip packing argument.
  for (let index = 1; index < points.length; index++) {
    if (points[index][0] === points[index - 1][0] &&
        points[index][1] === points[index - 1][1]) {
      consider(points[index - 1], points[index]);
    }
  }
  if (distance === 0) return pair;

  function recurse(part) {
    if (part.length <= 3) {
      for (let i = 0; i < part.length; i++) {
        for (let j = 0; j < i; j++) consider(part[i], part[j]);
      }
      return part.slice().sort((a, b) => a[1] - b[1]);
    }
    const middle = Math.floor(part.length / 2);
    const centerX = part[middle][0];
    const left = recurse(part.slice(0, middle));
    const right = recurse(part.slice(middle));
    const merged = [];
    let i = 0;
    let j = 0;
    while (i < left.length || j < right.length) {
      if (j === right.length || (i < left.length && left[i][1] <= right[j][1])) {
        merged.push(left[i++]);
      } else {
        merged.push(right[j++]);
      }
    }
    const strip = merged.filter(point => Math.abs(point[0] - centerX) <= distance);
    for (let i = 0; i < strip.length; i++) {
      for (let j = i - 1; j >= 0 && strip[i][1] - strip[j][1] <= distance; j--) {
        consider(strip[i], strip[j]);
      }
    }
    return merged;
  }
  recurse(points);
  return pair;
}

module.exports = solve;
