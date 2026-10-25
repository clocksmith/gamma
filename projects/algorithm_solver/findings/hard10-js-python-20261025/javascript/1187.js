/**
 * 1187. Make Array Strictly Increasing (Hard).
 * Fresh candidate authored in this conversation; no repository solution copied.
 * Specification: https://leetcode.com/problems/make-array-strictly-increasing/description/
 * Canonical API: solve(arr1, arr2); native alias: makeArrayIncreasing(arr1, arr2).
 * Inputs are preserved. Gamma independent qualification is pending.
 */
'use strict';

function solve(arr1, arr2) {
  const replacements = Array.from(new Set(arr2)).sort((left, right) => left - right);

  function firstGreater(value) {
    let low = 0;
    let high = replacements.length;
    while (low < high) {
      const middle = low + Math.floor((high - low) / 2);
      if (replacements[middle] <= value) {
        low = middle + 1;
      } else {
        high = middle;
      }
    }
    return low;
  }

  // Index is replacement count; value is the smallest possible final element.
  let smallestTail = [-1];
  for (const value of arr1) {
    const next = new Array(smallestTail.length + 1).fill(Infinity);
    for (let count = 0; count < smallestTail.length; count++) {
      const previous = smallestTail[count];
      if (previous === Infinity) {
        continue;
      }
      if (value > previous) {
        next[count] = Math.min(next[count], value);
      }
      const replacementIndex = firstGreater(previous);
      if (replacementIndex < replacements.length) {
        next[count + 1] = Math.min(next[count + 1], replacements[replacementIndex]);
      }
    }

    // A no-cheaper state with a no-smaller tail can never improve a suffix.
    let bestTail = Infinity;
    for (let count = 0; count < next.length; count++) {
      if (next[count] >= bestTail) {
        next[count] = Infinity;
      } else {
        bestTail = next[count];
      }
    }
    while (next.length > 0 && next[next.length - 1] === Infinity) {
      next.pop();
    }
    if (next.length === 0) {
      return -1;
    }
    smallestTail = next;
  }
  return smallestTail.findIndex(value => value !== Infinity);
}

function makeArrayIncreasing(arr1, arr2) {
  return solve(arr1, arr2);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, makeArrayIncreasing };
}
