"use strict";
// Hack2Hire 6a00c4cbf1b0b7030ba32383 (Rank Songs by Popularity) over an INFERRED spec; qualification unknown.

function solve(pref) {
  const m = pref[0].length;
  const votes = Array.from({length: m}, () => new Array(m).fill(0)); // votes[song][position]
  for (const p of pref) p.forEach((song, pos) => { votes[song][pos] += 1; });
  const ids = Array.from({length: m}, (_, s) => s);
  return ids.sort((a, b) => {
    const x = votes[a], y = votes[b];
    for (let i = 0; i < m; i++) if (x[i] !== y[i]) return y[i] - x[i];
    return a - b;
  });
}

function rankSongs(pref) { return solve(pref); }

module.exports = solve;
module.exports.rankSongs = rankSongs;
