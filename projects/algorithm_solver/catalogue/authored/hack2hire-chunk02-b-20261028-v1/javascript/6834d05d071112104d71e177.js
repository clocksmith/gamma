"use strict";
// Original Hack2Hire 6834d05d071112104d71e177 variant over an INFERRED specification; qualification unknown.
function solve(encoded) {
  const n = encoded.length, results = [], parts = [];
  const walk = (i, previous) => {
    if (i === n) { results.push(parts.join("")); return; }
    for (const size of [1, 2]) {
      if (i + size < n && encoded[i] !== "0") {
        const digit = encoded[i + size];
        if (digit !== previous) {
          parts.push(digit.repeat(Number(encoded.slice(i, i + size))));
          walk(i + size + 1, digit);
          parts.pop();
        }
      }
    }
  };
  walk(0, "");
  return results.sort();
}
function reverseCountAndSay(encoded) { return solve(encoded); }
module.exports = solve;
module.exports.reverseCountAndSay = reverseCountAndSay;
