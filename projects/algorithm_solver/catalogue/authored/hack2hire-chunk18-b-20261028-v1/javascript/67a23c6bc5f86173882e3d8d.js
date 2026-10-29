"use strict";
// Hack2Hire 67a23c6bc5f86173882e3d8d (Regex Pattern Matching) over an INFERRED spec; qualification unknown.

function units_(pattern) {
  const units = [];
  let i = 0;
  const n = pattern.length;
  while (i < n) {
    let body;
    if (pattern[i] === "(") {
      const j = pattern.indexOf(")", i);
      body = pattern.slice(i + 1, j);
      i = j + 1;
    } else {
      body = pattern[i];
      i += 1;
    }
    const star = i < n && pattern[i] === "*";
    if (star) i += 1;
    units.push([body, star]);
  }
  return units;
}

function solve(text, pattern) {
  const units = units_(pattern);
  const n = text.length, u = units.length;
  const dp = new Array(n + 1);  // dp[i][j]: text[i:] matches units[j:]
  for (let i = n; i >= 0; i--) {
    const row = new Array(u + 1).fill(false);
    row[u] = i === n;
    for (let j = u - 1; j >= 0; j--) {
      const [body, star] = units[j];
      const g = body.length;
      let fits;
      if (g === 1) fits = i < n && (body === "." || body === text[i]);
      else {
        fits = i + g <= n;
        if (fits) {
          for (let k = 0; k < g; k++) {
            const c = body[k];
            if (c !== "." && c !== text[i + k]) { fits = false; break; }
          }
        }
      }
      if (star) row[j] = row[j + 1] || (fits && dp[i + g][j]);
      else row[j] = fits && dp[i + g][j + 1];
    }
    dp[i] = row;
  }
  return dp[0][0];
}

function isMatch(text, pattern) { return solve(text, pattern); }

module.exports = solve;
module.exports.isMatch = isMatch;
