"use strict";
// Hack2Hire 677de8b2052a260e0165706a (Organize Books to Shelves) over an INFERRED spec; qualification unknown.

function solve(numShelves, limit) {
  // Counts stay non-increasing by shelf index, so the target for a prefix is the first shelf holding count[limit - 1].
  const count = new Array(numShelves).fill(0);
  const first = new Map([[0, 0]]); // count value -> smallest shelf index holding it
  const out = [];
  for (const lim of limit) {
    const v = count[lim - 1];
    const j = first.get(v);
    out.push(j);
    count[j] = v + 1;
    if (j + 1 < numShelves && count[j + 1] === v) first.set(v, j + 1); else first.delete(v);
    if (!first.has(v + 1)) first.set(v + 1, j);
  }
  return out;
}

function organizeBooks(numShelves, limit) { return solve(numShelves, limit); }

module.exports = solve;
module.exports.organizeBooks = organizeBooks;
