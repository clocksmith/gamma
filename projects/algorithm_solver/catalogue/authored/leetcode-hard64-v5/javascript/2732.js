'use strict';

// 2732. Find a Good Subset of the Matrix. Find a zero row or two disjoint row masks in the at-most-five-column domain; O(m*n+4^n) time and O(2^n) space for n<=5. Inputs are preserved.

function solve(grid) {
  const first = new Map();
  for (let index = 0; index < grid.length; index += 1) {
    let mask = 0;
    for (let column = 0; column < grid[index].length; column += 1) mask |= grid[index][column] << column;
    if (mask === 0) return [index];
    if (!first.has(mask)) first.set(mask, index);
  }
  const masks = Array.from(first.keys());
  for (let index = 0; index < masks.length; index += 1) {
    for (let other = index + 1; other < masks.length; other += 1) {
      if ((masks[index] & masks[other]) === 0) return [first.get(masks[index]), first.get(masks[other])].sort((a, b) => a - b);
    }
  }
  return [];
}

const goodSubsetofBinaryMatrix = solve;
class Solution {
  goodSubsetofBinaryMatrix(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, goodSubsetofBinaryMatrix };
