"use strict";
// Hack2Hire 67a2d68216a8465483dca727 (Process Queue) over an INFERRED spec; qualification unknown.

function solve(wait) {
  const n = wait.length, sizes = [n];
  const bucket = new Int32Array(n + 2); // unprocessed processes per wait value (only waits <= n can expire in time)
  for (const w of wait) if (w <= n) bucket[w]++;
  const processed = new Uint8Array(n);
  let alive = n, front = 0, t = 0;
  while (alive) {
    t++;
    while (processed[front] || wait[front] <= t - 1) front++;
    processed[front] = 1;
    alive--;
    if (wait[front] <= n) bucket[wait[front]]--;
    front++;
    alive -= bucket[t];
    sizes.push(alive);
  }
  return sizes;
}

function processQueue(wait) { return solve(wait); }

module.exports = solve;
module.exports.processQueue = processQueue;
