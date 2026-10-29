"use strict";
// Hack2Hire 685303fe1af0034b3227652e (Find Path in Fibonacci Tree) over an INFERRED spec; qualification unknown.

function solve(n, startValue, destValue) {
  const size = [0, 1]; // S(0) = 0, S(1) = 1, S(m) = 1 + S(m - 2) + S(m - 1)
  for (let m = 2; m <= n; m++) size.push(1 + size[m - 2] + size[m - 1]);
  const steps = (label) => {
    const out = [];
    let order = n;
    while (label) {
      label -= 1; // skip the current root in pre-order
      if (label < size[order - 2]) { out.push("L"); order -= 2; }
      else { label -= size[order - 2]; out.push("R"); order -= 1; }
    }
    return out;
  };
  const a = steps(startValue), b = steps(destValue);
  let i = 0;
  while (i < a.length && i < b.length && a[i] === b[i]) i++;
  return "U".repeat(a.length - i) + b.slice(i).join("");
}

function findPath(n, startValue, destValue) { return solve(n, startValue, destValue); }

module.exports = solve;
module.exports.findPath = findPath;
