/**
 * 10. Regular Expression Matching (Hard).
 * Fresh candidate authored in this conversation; no repository solution copied.
 * Specification: https://leetcode.com/problems/regular-expression-matching/description/
 * Canonical API: solve(s, p); native alias: isMatch(s, p).
 * Inputs are preserved. Gamma independent qualification is pending.
 */
'use strict';

function solve(s, p) {
  const patternLength = p.length;
  let previous = new Array(patternLength + 1).fill(false);
  previous[0] = true;
  for (let column = 2; column <= patternLength; column++) {
    if (p[column - 1] === '*') {
      previous[column] = previous[column - 2];
    }
  }

  for (let row = 1; row <= s.length; row++) {
    const current = new Array(patternLength + 1).fill(false);
    for (let column = 1; column <= patternLength; column++) {
      if (p[column - 1] === '*') {
        const atom = p[column - 2];
        const matches = atom === '.' || atom === s[row - 1];
        current[column] = current[column - 2] ||
          (matches && previous[column]);
      } else {
        const matches = p[column - 1] === '.' ||
          p[column - 1] === s[row - 1];
        current[column] = matches && previous[column - 1];
      }
    }
    previous = current;
  }
  return previous[patternLength];
}

function isMatch(s, p) {
  return solve(s, p);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, isMatch };
}
