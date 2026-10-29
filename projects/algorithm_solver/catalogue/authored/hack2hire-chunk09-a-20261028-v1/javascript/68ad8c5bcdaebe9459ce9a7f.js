"use strict";
// Hack2Hire 68ad8c5bcdaebe9459ce9a7f (Validate  Playlist Sequence) over an INFERRED spec; qualification unknown.

function solve(numSongs, sequence) {
  const n = numSongs;
  const last = new Map();
  const cover = new Array(n + 1).fill(0);
  let arcs = 0;
  for (let i = 0; i < sequence.length; i++) {
    const song = sequence[i];
    const j = last.get(song);
    last.set(song, i);
    if (j === undefined || i - j >= n) continue;
    arcs += 1;
    const lo = (j + 1) % n, hi = i % n; // allowed cut residues lo..hi, wrapping
    if (lo <= hi) { cover[lo] += 1; cover[hi + 1] -= 1; }
    else { cover[lo] += 1; cover[n] -= 1; cover[0] += 1; cover[hi + 1] -= 1; }
  }
  if (arcs === 0) return true;
  let running = 0;
  for (let r = 0; r < n; r++) {
    running += cover[r];
    if (running === arcs) return true;
  }
  return false;
}

function isShuffleSequence(numSongs, sequence) { return solve(numSongs, sequence); }

module.exports = solve;
module.exports.isShuffleSequence = isShuffleSequence;
