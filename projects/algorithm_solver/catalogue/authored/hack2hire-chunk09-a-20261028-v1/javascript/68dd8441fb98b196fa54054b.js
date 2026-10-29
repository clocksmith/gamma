"use strict";
// Hack2Hire 68dd8441fb98b196fa54054b (Build Smallest Number, variant 1 of 2) over an INFERRED spec; qualification unknown.

function solve(digits) {
  const count = new Array(10).fill(0);
  for (const d of digits) count[d] += 1;
  let first = 1;
  while (first < 10 && count[first] === 0) first += 1;
  if (first === 10) return "0";
  count[first] -= 1;
  const parts = [String(first)];
  for (let d = 0; d < 10; d++) parts.push(String(d).repeat(count[d]));
  return parts.join("");
}

function smallestNumber(digits) { return solve(digits); }

module.exports = solve;
module.exports.smallestNumber = smallestNumber;
