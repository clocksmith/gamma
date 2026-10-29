"use strict";

function solve(length, updates) {
  const diff = new Int32Array(length + 1);
  for (let i = 0; i < updates.length; i++) {
    const [l, r, inc] = updates[i];
    diff[l] += inc;
    diff[r + 1] -= inc;
  }
  const res = new Array(length);
  let cur = 0;
  for (let i = 0; i < length; i++) {
    cur += diff[i];
    res[i] = cur;
  }
  return res;
}

function getModifiedArray(length, updates) {
  return solve(length, updates);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.getModifiedArray = getModifiedArray;
