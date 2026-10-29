"use strict";

function solve(low, high) {
  const res = low === 0 ? [0] : [];
  const q = [1, 2, 3, 4, 5, 6, 7, 8, 9];
  for (let i = 0; i < q.length; i++) {
    const v = q[i];
    if (v > high) continue;
    if (v >= low) res.push(v);
    const last = v % 10;
    if (last > 0 && v * 10 + last - 1 <= high) q.push(v * 10 + last - 1);
    if (last < 9 && v * 10 + last + 1 <= high) q.push(v * 10 + last + 1);
  }
  res.sort((a, b) => a - b);
  return res;
}

function countSteppingNumbers(low, high) {
  return solve(low, high);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.countSteppingNumbers = countSteppingNumbers;
