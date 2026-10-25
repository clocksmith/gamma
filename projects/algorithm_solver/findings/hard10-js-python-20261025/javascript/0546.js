/**
 * 546. Remove Boxes (Hard).
 * Fresh candidate authored in this conversation; no repository solution copied.
 * Specification: https://leetcode.com/problems/remove-boxes/description/
 * Canonical API: solve(boxes); native alias: removeBoxes(boxes).
 * Inputs are preserved. Gamma independent qualification is pending.
 */
'use strict';

function solve(boxes) {
  const colors = [];
  const counts = [];
  for (const color of boxes) {
    if (colors.length > 0 && colors[colors.length - 1] === color) {
      counts[counts.length - 1]++;
    } else {
      colors.push(color);
      counts.push(1);
    }
  }
  const groupCount = colors.length;
  const carryBase = boxes.length + 1;
  const memo = new Map();

  function bestScore(left, right, carried) {
    if (left > right) {
      return 0;
    }
    const key = (left * groupCount + right) * carryBase + carried;
    if (memo.has(key)) {
      return memo.get(key);
    }
    const mergedCount = counts[right] + carried;
    let best = bestScore(left, right - 1, 0) + mergedCount * mergedCount;
    for (let middle = left; middle < right; middle++) {
      if (colors[middle] === colors[right]) {
        best = Math.max(
          best,
          bestScore(left, middle, mergedCount) +
            bestScore(middle + 1, right - 1, 0)
        );
      }
    }
    memo.set(key, best);
    return best;
  }

  return bestScore(0, groupCount - 1, 0);
}

function removeBoxes(boxes) {
  return solve(boxes);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, removeBoxes };
}
