// Original implementation. Contract: https://leetcode.com/problems/number-of-ways-to-build-sturdy-brick-wall/
"use strict";

function solve(height, width, bricks) {
  const MOD = 1000000007;
  const masks = [];
  function build(position, seams) {
    if (position === width) {
      masks.push(seams);
      return;
    }
    for (const brick of bricks) {
      const next = position + brick;
      if (next <= width) build(next, seams | (next < width ? 1 << next : 0));
    }
  }
  build(0, 0);
  const compatible = masks.map(first => masks
    .map((second, index) => (first & second) ? -1 : index)
    .filter(index => index >= 0));
  let ways = masks.map(() => 1);
  for (let row = 1; row < height; row++) {
    ways = compatible.map(indices => indices.reduce((sum, index) => (sum + ways[index]) % MOD, 0));
  }
  return ways.reduce((sum, count) => (sum + count) % MOD, 0);
}

module.exports = solve;
