'use strict';

// 3873. Maximum Points Activated with One Addition.
// O(n alpha(n)) expected time and O(n) space; one new point can connect the two largest coordinate components.
function solve(points) {
  const n = points.length;
  const parent = Array.from({ length: n }, (_, index) => index);
  const sizes = Array(n).fill(1);
  function find(node) {
    while (node !== parent[node]) {
      parent[node] = parent[parent[node]];
      node = parent[node];
    }
    return node;
  }
  function union(left, right) {
    left = find(left);
    right = find(right);
    if (left === right) return;
    if (sizes[left] < sizes[right]) [left, right] = [right, left];
    parent[right] = left;
    sizes[left] += sizes[right];
  }
  const xs = new Map();
  const ys = new Map();
  for (let index = 0; index < n; index += 1) {
    const [x, y] = points[index];
    if (xs.has(x)) union(index, xs.get(x));
    else xs.set(x, index);
    if (ys.has(y)) union(index, ys.get(y));
    else ys.set(y, index);
  }
  let largest = 0;
  let second = 0;
  for (let index = 0; index < n; index += 1) {
    if (parent[index] !== index) continue;
    const size = sizes[index];
    if (size >= largest) {
      second = largest;
      largest = size;
    } else if (size > second) second = size;
  }
  return largest + second + 1;
}

const maxActivated = solve;
class Solution {
  maxActivated(points) { return solve(points); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxActivated };
