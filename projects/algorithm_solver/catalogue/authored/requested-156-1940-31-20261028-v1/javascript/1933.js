"use strict";

// string_unit = unicode_codepoint: a non-BMP character is one unit, matching
// Python str and the reference. The Array.from copy is charged as O(n) space.
function solve(s) {
  const chars = Array.from(s);
  let twos = 0;
  let i = 0;
  const n = chars.length;
  while (i < n) {
    let j = i;
    while (j < n && chars[j] === chars[i]) j++;
    const rem = (j - i) % 3;
    if (rem === 1) return false;
    if (rem === 2) twos++;
    i = j;
  }
  return twos === 1;
}

function isDecomposable(s) {
  return solve(s);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.isDecomposable = isDecomposable;
if (typeof Solution !== "undefined") solve.Solution = Solution;
