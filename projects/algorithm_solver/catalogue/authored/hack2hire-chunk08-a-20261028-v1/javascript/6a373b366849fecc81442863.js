"use strict";
// Hack2Hire 6a373b366849fecc81442863 (Repair Bootloader Program, variant 2 of 2) over an INFERRED spec; qualification unknown.

const PLUS = 0, NEXT = 1, JUMP = 2, CODE = {plus: PLUS, next: NEXT, jump: JUMP};

function solve(instructions) {
  const n = instructions.length, ops = new Uint8Array(n), vals = new Int32Array(n);
  instructions.forEach((line, i) => { const [op, value] = line.split(" "); ops[i] = CODE[op]; vals[i] = Number(value); });
  const target = new Int32Array(n), start = new Int32Array(n + 2), preds = new Int32Array(n);
  for (let i = 0; i < n; i++) {
    const t = ops[i] === JUMP ? i + vals[i] : i + 1;
    target[i] = t;
    if (t >= 0 && t <= n) start[t + 1]++;
  }
  for (let t = 0; t <= n; t++) start[t + 1] += start[t];
  const fill = start.slice(0, n + 1);
  for (let i = 0; i < n; i++) if (target[i] >= 0 && target[i] <= n) preds[fill[target[i]]++] = i;
  const good = new Uint8Array(n + 1), stack = [n]; // good[i]: the unmodified program reaches index n from i
  good[n] = 1;
  while (stack.length) {
    const t = stack.pop();
    for (let p = start[t]; p < start[t + 1]; p++) {
      const i = preds[p];
      if (!good[i]) { good[i] = 1; stack.push(i); }
    }
  }
  const seen = new Uint8Array(n);
  let i = 0, best = -1;
  while (i >= 0 && i < n && !seen[i]) {
    seen[i] = 1;
    if (ops[i] !== PLUS) {
      const t = ops[i] === JUMP ? i + 1 : i + vals[i];
      if (t >= 0 && t <= n && good[t] && (best < 0 || i < best)) best = i;
    }
    i = target[i];
  }
  if (best < 0) return [-1, 0];
  let acc = 0;
  i = 0;
  while (i !== n) {
    let op = ops[i];
    if (i === best) op = op === JUMP ? NEXT : JUMP;
    if (op === JUMP) i += vals[i];
    else { if (op === PLUS) acc += vals[i]; i += 1; }
  }
  return [best, acc];
}

function repairProgram(instructions) { return solve(instructions); }

module.exports = solve;
module.exports.repairProgram = repairProgram;
