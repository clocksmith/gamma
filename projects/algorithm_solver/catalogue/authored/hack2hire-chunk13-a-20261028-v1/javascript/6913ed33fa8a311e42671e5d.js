"use strict";
// Hack2Hire 6913ed33fa8a311e42671e5d (Pin Board Connectivity, variant 2) over an INFERRED spec; qualification unknown.

function solve(boards, pin1, pin2) {
  const on = new Map(); // pin -> indices of the boards holding it
  boards.forEach((board, b) => {
    for (const pin of board) { let list = on.get(pin); if (!list) on.set(pin, list = []); list.push(b); }
  });
  if (!on.has(pin1) || !on.has(pin2)) return -1;
  const dist = new Array(boards.length).fill(0); // 0 = not reached
  const queue = [];
  for (const b of on.get(pin1)) { dist[b] = 1; queue.push(b); }
  const expanded = new Set([pin1]);
  for (let head = 0; head < queue.length; head++) {
    const b = queue[head];
    for (const pin of boards[b]) {
      if (pin === pin2) return dist[b];
      if (expanded.has(pin)) continue;
      expanded.add(pin);
      for (const nb of on.get(pin)) if (dist[nb] === 0) { dist[nb] = dist[b] + 1; queue.push(nb); }
    }
  }
  return -1;
}

function minBoardsBetweenPins(boards, pin1, pin2) { return solve(boards, pin1, pin2); }

module.exports = solve;
module.exports.minBoardsBetweenPins = minBoardsBetweenPins;
