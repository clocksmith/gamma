"use strict";
// Hack2Hire 67e3915487527b3f41af78b6 (Keypad Letter Combination) over an INFERRED spec; qualification unknown.

const KEYPAD = {1: "ABC", 2: "DEF", 3: "GHI", 4: "JKL", 5: "MNO", 6: "PQR", 7: "ST", 8: "UVW", 9: "XY", 0: "Z"};

function solve(digits) {
  const n = digits.length;
  if (n === 0) return [];
  const out = [], letters = [];
  function extend(i) {
    // smaller groups give smaller letters, so results come out in lexicographic order
    if (i === n) { out.push(letters.join("")); return; }
    const keys = KEYPAD[digits[i]];
    for (let g = 1; g <= keys.length && i + g <= n && digits[i + g - 1] === digits[i]; g++) {
      letters.push(keys[g - 1]);
      extend(i + g);
      letters.pop();
    }
  }
  extend(0);
  return out;
}

function letterCombinations(digits) { return solve(digits); }

module.exports = solve;
module.exports.letterCombinations = letterCombinations;
