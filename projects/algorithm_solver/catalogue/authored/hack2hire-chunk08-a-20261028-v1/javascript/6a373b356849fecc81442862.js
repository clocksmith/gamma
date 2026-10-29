"use strict";
// Hack2Hire 6a373b356849fecc81442862 (Repair Bootloader Program, variant 1 of 2) over an INFERRED spec; qualification unknown.

const PLUS = 0, NEXT = 1, JUMP = 2, CODE = {plus: PLUS, next: NEXT, jump: JUMP};

function solve(instructions) {
  const n = instructions.length, ops = new Uint8Array(n), vals = new Int32Array(n);
  instructions.forEach((line, i) => { const [op, value] = line.split(" "); ops[i] = CODE[op]; vals[i] = Number(value); });
  const seen = new Uint8Array(n);
  let i = 0, acc = 0;
  while (i >= 0 && i < n) {
    if (seen[i]) return [i, acc];
    seen[i] = 1;
    if (ops[i] === JUMP) i += vals[i];
    else { if (ops[i] === PLUS) acc += vals[i]; i += 1; }
  }
  return [-1, acc];
}

function findLoop(instructions) { return solve(instructions); }

module.exports = solve;
module.exports.findLoop = findLoop;
