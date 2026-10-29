"use strict";
// Hack2Hire 6862ed30eb0810914237aaf3 (Add Signed Arrays) over an INFERRED spec; qualification unknown.

function parse(chars) {
  let sign = 1, start = 0, value = 0;
  if (chars[0] === '-') { sign = -1; start = 1; }
  for (let i = start; i < chars.length; i++) value = value * 10 + (chars[i].charCodeAt(0) - 48);
  return sign * value + 0;
}

function solve(a, b) { return parse(a) + parse(b) + 0; }

function addSignedArrays(a, b) { return solve(a, b); }

module.exports = solve;
module.exports.addSignedArrays = addSignedArrays;
