"use strict";
// Hack2Hire 6a4d62db60d5cca82da2fdda (Beam Search Decoding, variant 2 of 2) over an INFERRED spec; qualification unknown.

function solve(scores, beamWidth) {
  let beam = [[0, 0, []]];  // [total, lexicographic rank, sequence], best first
  for (const row of scores) {
    const tokens = row.map((_, j) => j).sort((x, y) => row[y] - row[x] || x - y).slice(0, beamWidth);
    const candidates = [];
    for (const [total, rank, seq] of beam) for (const j of tokens) candidates.push([total + row[j], rank, j, seq]);
    candidates.sort((x, y) => y[0] - x[0] || x[1] - y[1] || x[2] - y[2]);
    const kept = candidates.slice(0, beamWidth);
    const order = kept.map((_, k) => k).sort((x, y) => kept[x][1] - kept[y][1] || kept[x][2] - kept[y][2]);
    const ranks = new Array(kept.length);
    order.forEach((k, r) => { ranks[k] = r; });
    beam = kept.map((c, k) => [c[0], ranks[k], c[3].concat([c[2]])]);
  }
  return beam.map((entry) => entry[2]);
}

function beamSearch(scores, beamWidth) { return solve(scores, beamWidth); }

module.exports = solve;
module.exports.beamSearch = beamSearch;
