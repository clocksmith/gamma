"use strict";

// string_unit = unicode_codepoint: a non-BMP character is one unit, matching
// Python str and the reference. The Array.from copy is charged as O(n) space.
function solve(s, t) {
  let a = Array.from(s), b = Array.from(t);
  if (a.length > b.length) {
    const tmp = a; a = b; b = tmp;
  }
  if (b.length - a.length > 1) return false;
  const tailEqual = (i, j) => {
    while (i < a.length && j < b.length && a[i] === b[j]) { i++; j++; }
    return i === a.length && j === b.length;
  };
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) {
      if (a.length === b.length) return tailEqual(i + 1, i + 1);
      return tailEqual(i, i + 1);
    }
  }
  return b.length === a.length + 1;
}

function isOneEditDistance(s, t) {
  return solve(s, t);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.isOneEditDistance = isOneEditDistance;
if (typeof Solution !== "undefined") solve.Solution = Solution;
