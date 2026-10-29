"use strict";

function solve(n, pick) {
  let low = 1;
  let high = Number(n);
  const g = pick === undefined && typeof globalThis.guess === "function" ? globalThis.guess : null;
  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    let res;
    if (pick !== undefined) {
      res = mid === pick ? 0 : (mid > pick ? -1 : 1);
    } else if (g !== null) {
      res = g(mid);
    } else {
      return mid;
    }
    if (res === 0) return mid;
    if (res < 0) high = mid - 1;
    else low = mid + 1;
  }
  return low;
}

function guessNumber(n, pick) {
  return solve(n, pick);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.guessNumber = guessNumber;
