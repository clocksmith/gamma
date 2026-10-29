"use strict";
// Hack2Hire 6a14eb4e7b0582b35278812d (String Matches in Matrix) over an INFERRED spec; qualification unknown.

function solve(matrix, s) {
  const m = matrix.length, n = matrix[0].length, k = s.length;
  const fail = new Array(k).fill(0);
  for (let i = 1, j = 0; i < k; i++) {
    while (j && s[i] !== s[j]) j = fail[j - 1];
    if (s[i] === s[j]) j += 1;
    fail[i] = j;
  }
  const occurrences = (line) => {
    let found = 0, state = 0;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      while (state && ch !== s[state]) state = fail[state - 1];
      if (ch === s[state]) state += 1;
      if (state === k) { found += 1; state = fail[state - 1]; }
    }
    return found;
  };
  let total = 0;
  if (k <= n) for (const row of matrix) total += occurrences(row);
  if (k <= m) {
    for (let c = 0; c < n; c++) {
      const column = new Array(m);
      for (let r = 0; r < m; r++) column[r] = matrix[r][c];
      total += occurrences(column.join(""));
    }
  }
  if (k <= m && k <= n) {
    const starts = [];
    for (let c = 0; c < n; c++) starts.push([0, c]);
    for (let r = 1; r < m; r++) starts.push([r, 0]);
    for (const [r, c] of starts) {
      const length = Math.min(m - r, n - c);
      if (length < k) continue;
      const diagonal = new Array(length);
      for (let i = 0; i < length; i++) diagonal[i] = matrix[r + i][c + i];
      total += occurrences(diagonal.join(""));
    }
  }
  return total;
}

function countMatches(matrix, s) { return solve(matrix, s); }

module.exports = solve;
module.exports.countMatches = countMatches;
