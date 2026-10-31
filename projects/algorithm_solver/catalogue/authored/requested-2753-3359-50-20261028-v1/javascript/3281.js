"use strict";

function solve(start, d) {
  const arr = start.slice().sort((a, b) => a - b);
  let lo = 0;
  let hi = arr[arr.length - 1] + d - arr[0];
  while (lo < hi) {
    const mid = Math.floor((lo + hi + 1) / 2);
    let prev = arr[0];
    let ok = true;
    for (let i = 1; i < arr.length; i++) {
      const nxt = prev + mid > arr[i] ? prev + mid : arr[i];
      if (nxt > arr[i] + d) {
        ok = false;
        break;
      }
      prev = nxt;
    }
    if (ok) lo = mid;
    else hi = mid - 1;
  }
  return lo;
}

function maxPossibleScore(start, d) {
  return solve(start, d);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.maxPossibleScore = maxPossibleScore;
