// Original candidate. Contract: https://leetcode.com/problems/amount-of-new-area-painted-each-day/
"use strict";

function solve(paint) {
  let maximum = 0;
  for (const [, end] of paint) maximum = Math.max(maximum, end);
  const successor = Array.from({length: maximum + 1}, (_, i) => i);

  // Each painted unit points to the next potentially unpainted unit.
  function find(x) {
    while (successor[x] !== x) {
      successor[x] = successor[successor[x]];
      x = successor[x];
    }
    return x;
  }

  return paint.map(([start, end]) => {
    let count = 0;
    let unit = find(start);
    while (unit < end) {
      count++;
      successor[unit] = find(unit + 1);
      unit = successor[unit];
    }
    return count;
  });
}

module.exports = solve;
