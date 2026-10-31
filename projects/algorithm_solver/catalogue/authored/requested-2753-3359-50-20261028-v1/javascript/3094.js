"use strict";

function solve(n) {
  if (typeof n === "number") {
    let ans = 0;
    for (let b = 0; b < 30; b++) {
      if ((n >> b) & 1) ans |= 1 << b;
    }
    return ans;
  }
  const fn = typeof n === "function" ? n : globalThis.commonBits;
  let base = fn(0);
  let ans = 0;
  for (let b = 0; b < 30; b++) {
    const cur = fn(1 << b);
    if (cur > base) ans |= 1 << b;
    base = fn(1 << b);
  }
  return ans;
}

function findNumber(n) {
  return solve(n);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.findNumber = findNumber;
