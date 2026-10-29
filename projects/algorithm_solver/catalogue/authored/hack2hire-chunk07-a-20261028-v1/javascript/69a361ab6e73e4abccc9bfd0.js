"use strict";
// Hack2Hire 69a361ab6e73e4abccc9bfd0 (Maximum Value of Valid Expression Path) over an INFERRED spec; qualification unknown.

function solve(matrix) {
  const m = matrix.length, n = matrix[0].length, NONE = -Infinity;
  const value = new Float64Array(m * n).fill(NONE);  // digit: best expression ending here; operator: best digit predecessor
  const isDigit = (ch) => ch >= "0" && ch <= "9";
  let best = NONE;
  for (let r = 0; r < m; r++) {
    for (let c = 0; c < n; c++) {
      const ch = matrix[r][c], at = r * n + c;
      if (isDigit(ch)) {
        const d = ch.charCodeAt(0) - 48;
        let cur = d;
        for (const [pr, pc] of [[r - 1, c], [r, c - 1]]) {
          if (pr < 0 || pc < 0) continue;
          const op = matrix[pr][pc], v = value[pr * n + pc];
          if (!isDigit(op) && v !== NONE) { const cand = op === "+" ? v + d : v - d; if (cand > cur) cur = cand; }
        }
        value[at] = cur;
        if (cur > best) best = cur;
      } else {
        let carried = NONE;
        for (const [pr, pc] of [[r - 1, c], [r, c - 1]]) {
          if (pr < 0 || pc < 0 || !isDigit(matrix[pr][pc])) continue;
          if (value[pr * n + pc] > carried) carried = value[pr * n + pc];
        }
        value[at] = carried;
      }
    }
  }
  return best;
}

function maxExpressionPathValue(matrix) { return solve(matrix); }

module.exports = solve;
module.exports.maxExpressionPathValue = maxExpressionPathValue;
