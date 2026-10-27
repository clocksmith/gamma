/* Original candidate for LeetCode 2647. Contract: https://leetcode.com/problems/color-the-triangle-red/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Returns [row,position] seeds, rows1..n and positions1..2row-1. Original four-row fringe construction; see independent construction note and infection tests. Ordering is noncanonical and immaterial.
Complexity: O(n²) time/output space */
"use strict";

function solve(n) {
  const seeds = [];
  while (n >= 4) {
    // Bottom-row upward cells fill the intervening downward cells.
    for (let column = 1; column < 2 * n; column += 2) {
      seeds.push([n, column]);
    }
    seeds.push([n - 1, 2 * n - 4]);
    for (const row of [n - 2, n - 3]) {
      for (let column = 1; column < 2 * row; column += 4) {
        const shift = n % 2 && row === n - 2 && column === 2 * n - 5;
        seeds.push([row, shift ? column - 1 : column]);
      }
    }
    n -= 4;
  }
  if (n >= 1) seeds.push([1, 1]);
  if (n >= 2) seeds.push([2, 1], [2, 3]);
  if (n === 3) seeds.push([3, 1], [3, 5]);
  return seeds;
}

module.exports = solve;
