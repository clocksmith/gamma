"use strict";

const PAIRS = [["0", "0"], ["1", "1"], ["6", "9"], ["8", "8"], ["9", "6"]];

function solve(low, high) {
  const lnLo = low.length, lnHi = high.length;
  let count = 0;
  for (let length = lnLo; length <= lnHi; length++) {
    let cur = length % 2 === 0 ? [""] : ["0", "1", "8"];
    let rem = length - (length % 2);
    while (rem > 0) {
      const isOuter = rem === 2;
      const nxt = [];
      for (let i = 0; i < cur.length; i++) {
        const s = cur[i];
        for (let j = 0; j < PAIRS.length; j++) {
          const [a, b] = PAIRS[j];
          if (isOuter && length > 1 && a === "0") continue;
          nxt.push(a + s + b);
        }
      }
      cur = nxt;
      rem -= 2;
    }
    for (let i = 0; i < cur.length; i++) {
      const s = cur[i];
      if ((s.length > lnLo || s >= low) && (s.length < lnHi || s <= high)) {
        count++;
      }
    }
  }
  return count;
}

function strobogrammaticInRange(low, high) {
  return solve(low, high);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.strobogrammaticInRange = strobogrammaticInRange;
