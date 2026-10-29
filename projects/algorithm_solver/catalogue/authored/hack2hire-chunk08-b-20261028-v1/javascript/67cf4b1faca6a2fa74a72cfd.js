"use strict";
// Hack2Hire 67cf4b1faca6a2fa74a72cfd (Set Parity Bits) over an INFERRED spec; qualification unknown.

function solve(byte) {
  const low = byte & 127;
  let x = low ^ (low >> 4);
  x ^= x >> 2;
  x ^= x >> 1;
  return low | ((x & 1) << 7);
}

function setParityBit(byte) { return solve(byte); }

module.exports = solve;
module.exports.setParityBit = setParityBit;
