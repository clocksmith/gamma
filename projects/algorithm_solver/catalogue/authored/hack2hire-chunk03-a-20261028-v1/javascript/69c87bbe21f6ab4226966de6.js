"use strict";
// Hack2Hire 69c87bbe21f6ab4226966de6 (Implement itoa()) over an INFERRED spec; qualification unknown.

function solve(value) {
  if (value === 0) return "0";
  const negative = value < 0;
  let magnitude = negative ? -value : value;
  const digits = [];
  while (magnitude > 0) {
    const digit = magnitude % 10;
    digits.push(String.fromCharCode(48 + digit));
    magnitude = (magnitude - digit) / 10;
  }
  if (negative) digits.push("-");
  return digits.reverse().join("");
}

function itoa(value) { return solve(value); }

module.exports = solve;
module.exports.itoa = itoa;
