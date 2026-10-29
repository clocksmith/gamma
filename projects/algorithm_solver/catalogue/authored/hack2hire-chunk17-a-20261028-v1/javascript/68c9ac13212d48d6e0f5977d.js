"use strict";
// Hack2Hire 68c9ac13212d48d6e0f5977d (Thrilling Teleporters, variant 2 of 2) over an INFERRED spec; qualification unknown.

function solve(teleporters, dieSides, lastSquare) {
  const target = new Int32Array(lastSquare);
  for (let i = 0; i < lastSquare; i++) target[i] = i;
  for (const entry of teleporters) {
    const comma = entry.indexOf(",");
    target[Number(entry.slice(0, comma))] = Number(entry.slice(comma + 1));
  }
  const dist = new Int32Array(lastSquare + 1).fill(-1);
  dist[0] = 0;
  const queue = new Int32Array(lastSquare + 1);
  let head = 0, tail = 0;
  queue[tail++] = 0;
  while (head < tail) {
    const square = queue[head++];
    const turns = dist[square] + 1;
    if (square + dieSides >= lastSquare) return turns;
    for (let roll = 1; roll <= dieSides; roll++) {
      const next = target[square + roll];
      if (next === lastSquare) return turns;
      if (dist[next] < 0) { dist[next] = turns; queue[tail++] = next; }
    }
  }
  return -1;
}

function minTurns(teleporters, dieSides, lastSquare) { return solve(teleporters, dieSides, lastSquare); }

module.exports = solve;
module.exports.minTurns = minTurns;
