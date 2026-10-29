// 521 — Longest Uncommon Subsequence I. Original implementation; authored candidate, not independently qualified.
function solve(a,b) { return a===b ? -1 : Math.max(a.length,b.length); }

module.exports = { solve, findLUSlength: solve };
