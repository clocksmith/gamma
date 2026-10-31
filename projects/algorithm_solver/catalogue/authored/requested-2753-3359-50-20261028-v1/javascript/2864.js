"use strict";

function solve(s) {
  let ones = 0;
  for (let i = 0; i < s.length; i++) {
    if (s.charCodeAt(i) === 49) ones++;
  }
  const zeros = s.length - ones;
  return "1".repeat(ones - 1) + "0".repeat(zeros) + "1";
}

function maximumOddBinaryNumber(s) {
  return solve(s);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.maximumOddBinaryNumber = maximumOddBinaryNumber;
