"use strict";
// Hack2Hire 69953e87312381f4e70fdb95 (Maximum Vacation With Minimum Flights) over an INFERRED spec; qualification unknown.

const better = (ad, af, bd, bf) => ad > bd || (ad === bd && af < bf);

function solve(days) {
  const m = days.length, n = days[0].length;
  let d = days.map((row) => row[0]), f = days.map((_, c) => (c === 0 ? 0 : 1));
  for (let w = 1; w < n; w++) {
    let first = -1, second = -1;
    for (let c = 0; c < m; c++) {
      if (first < 0 || better(d[c], f[c], d[first], f[first])) { second = first; first = c; }
      else if (second < 0 || better(d[c], f[c], d[second], f[second])) second = c;
    }
    const nd = new Array(m), nf = new Array(m);
    for (let c = 0; c < m; c++) {
      const src = first !== c ? first : second;
      let bd = d[c], bf = f[c];
      if (src >= 0 && better(d[src], f[src] + 1, bd, bf)) { bd = d[src]; bf = f[src] + 1; }
      nd[c] = bd + days[c][w]; nf[c] = bf;
    }
    d = nd; f = nf;
  }
  let best = 0;
  for (let c = 1; c < m; c++) if (better(d[c], f[c], d[best], f[best])) best = c;
  return [d[best], f[best]];
}

function maxVacation(days) { return solve(days); }

module.exports = solve;
module.exports.maxVacation = maxVacation;
