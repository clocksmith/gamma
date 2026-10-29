"use strict";
// Hack2Hire 6a1f2f7c8b879849ebc10f9a (Circular Storage Allocator) over an INFERRED spec; qualification unknown.

function solve(totalSlots, requests) {
  const used = new Array(totalSlots).fill(false);
  let freeCount = totalSlots;
  const result = [];
  for (const [kind, startText, sizeText] of requests) {
    const start = Number(startText), size = Number(sizeText);
    if (kind === "store") {
      let found = -1;
      if (freeCount >= size) {
        let run = 0;
        for (let offset = 0; offset < totalSlots + size - 1; offset++) {
          if (used[(start + offset) % totalSlots]) { run = 0; continue; }
          run++;
          if (run >= size) { found = (start + offset - size + 1) % totalSlots; break; }
        }
      }
      if (found >= 0) {
        for (let j = 0; j < size; j++) used[(found + j) % totalSlots] = true;
        freeCount -= size;
      }
      result.push(found);
    } else {
      let freed = 0;
      for (let j = 0; j < size; j++) {
        const q = (start + j) % totalSlots;
        if (used[q]) { used[q] = false; freed++; }
      }
      freeCount += freed;
      result.push(freed);
    }
  }
  return result;
}

function processRequests(totalSlots, requests) { return solve(totalSlots, requests); }

module.exports = solve;
module.exports.processRequests = processRequests;
