"use strict";

function solve(arrays) {
  const m = arrays.length;
  const cnt = new Map();
  for (let i = 0; i < m; i++) {
    const arr = arrays[i];
    for (let j = 0; j < arr.length; j++) {
      cnt.set(arr[j], (cnt.get(arr[j]) || 0) + 1);
    }
  }
  const res = [];
  const first = arrays[0];
  for (let j = 0; j < first.length; j++) {
    if (cnt.get(first[j]) === m) res.push(first[j]);
  }
  return res;
}

function longestCommonSubsequence(arrays) {
  return solve(arrays);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.longestCommonSubsequence = longestCommonSubsequence;
