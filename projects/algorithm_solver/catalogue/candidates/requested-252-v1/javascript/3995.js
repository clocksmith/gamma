'use strict';

// 3995. Minimum Cost to Convert String III.
// Specification: https://leetcode.com/problems/minimum-cost-to-convert-string-iii/description/
// O(n*R*L) time and O(n+R) auxiliary space; disjoint replacements, not transitive rule closure. Inputs are preserved.
function solve(source, target, rules, costs) {
  const size = source.length;
  const candidates = Array.from({ length: 26 }, () => []);
  for (let index = 0; index < rules.length; index++) {
    const [pattern, replacement] = rules[index];
    let price = costs[index];
    for (const character of pattern) if (character === '*') price++;
    candidates[replacement.charCodeAt(0) - 97].push([pattern, replacement, price]);
  }
  const best = new Float64Array(size + 1).fill(Infinity);
  best[0] = 0;
  for (let start = 0; start < size; start++) {
    if (!Number.isFinite(best[start])) continue;
    if (source[start] === target[start]) best[start + 1] = Math.min(best[start + 1], best[start]);
    for (const [pattern, replacement, price] of candidates[target.charCodeAt(start) - 97]) {
      if (start + pattern.length > size) continue;
      let matches = true;
      for (let offset = 0; offset < pattern.length; offset++) {
        if (replacement[offset] !== target[start + offset] || (pattern[offset] !== '*' && pattern[offset] !== source[start + offset])) {
          matches = false;
          break;
        }
      }
      if (matches) best[start + pattern.length] = Math.min(best[start + pattern.length], best[start] + price);
    }
  }
  return Number.isFinite(best[size]) ? best[size] : -1;
}

if (typeof module !== 'undefined') module.exports = { solve };
