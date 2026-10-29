"use strict";
// Hack2Hire 6907b46fe1919109b6df119a (Pandigital Sum) over an INFERRED spec; qualification unknown.

const COLUMNS = [[2, 5, 8], [1, 4, 7], [0, 3, 6]];

function solve(pattern) {
  const fixed = [];
  let used = 0;
  for (const c of pattern) {
    const d = c === "?" ? 0 : c.charCodeAt(0) - 48;
    fixed.push(d);
    if (d) used |= 1 << d;
  }
  const options = (position, mask) => {
    if (fixed[position]) return [fixed[position]];
    const out = [];
    for (let d = 1; d <= 9; d++) if (!((mask >> d) & 1)) out.push(d);
    return out;
  };
  const go = (column, carry, mask) => {
    if (column === 3) return carry === 0 ? 1 : 0;
    const [aPos, bPos, sPos] = COLUMNS[column];
    let total = 0;
    for (const a of options(aPos, mask)) {
      const maskA = mask | (1 << a);
      for (const b of options(bPos, maskA)) {
        if (b === a) continue;
        const maskB = maskA | (1 << b);
        const t = a + b + carry;
        const d = t % 10;
        if (d === 0 || d === a || d === b) continue;
        if (fixed[sPos]) { if (fixed[sPos] !== d) continue; }
        else if ((maskB >> d) & 1) continue;
        total += go(column + 1, t >= 10 ? 1 : 0, maskB | (1 << d));
      }
    }
    return total;
  };
  return go(0, 0, used);
}

function countPandigitalSums(pattern) { return solve(pattern); }

module.exports = solve;
module.exports.countPandigitalSums = countPandigitalSums;
