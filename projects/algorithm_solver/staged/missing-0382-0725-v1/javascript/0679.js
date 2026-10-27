'use strict';

// 679. 24 Game. Enumerate binary expression trees with exact rational arithmetic.

function solve(cards) {
  function gcd(a, b) { if (a < 0n) a = -a; if (b < 0n) b = -b; while (b !== 0n) [a, b] = [b, a % b]; return a; }
  function fraction(n, d = 1n) {
    if (d < 0n) { n = -n; d = -d; }
    const common = gcd(n, d); return [n / common, d / common];
  }
  function search(values) {
    if (values.length === 1) return values[0][0] === 24n * values[0][1];
    for (let i = 0; i < values.length; i += 1) for (let j = i + 1; j < values.length; j += 1) {
      const [a, b] = values[i], [c, d] = values[j];
      const rest = values.filter((_, k) => k !== i && k !== j);
      const candidates = [fraction(a * d + c * b, b * d), fraction(a * d - c * b, b * d),
        fraction(c * b - a * d, b * d), fraction(a * c, b * d)];
      if (c !== 0n) candidates.push(fraction(a * d, b * c));
      if (a !== 0n) candidates.push(fraction(c * b, d * a));
      const seen = new Set();
      for (const candidate of candidates) {
        const key = candidate.join('/');
        if (seen.has(key)) continue;
        seen.add(key);
        if (search(rest.concat([candidate]))) return true;
      }
    }
    return false;
  }
  return search(cards.map(value => fraction(BigInt(value))));
}

const judgePoint24 = solve;
class Solution {
  judgePoint24(cards) { return solve(cards); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, judgePoint24 };
