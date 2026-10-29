"use strict";
// Hack2Hire 6a1a0f0dc81f779dc6a2377e (Implement Dataset Join Operation, variant 4 of 4) over an INFERRED spec; qualification unknown.

function solve(customerFile, processorFile, fieldNames) {
  const customerHeader = customerFile[0].split(","), processorHeader = processorFile[0].split(",");
  const ci = fieldNames.map((f) => customerHeader.indexOf(f)), pi = fieldNames.map((f) => processorHeader.indexOf(f));
  const index = new Map(); // composite key (values joined by a comma, which values never contain) -> processor rows
  for (let r = 1; r < processorFile.length; r++) {
    const values = processorFile[r].split(","), key = pi.map((i) => values[i]).join(",");
    if (!index.has(key)) index.set(key, []);
    index.get(key).push(processorFile[r]);
  }
  const out = [customerFile[0] + "," + processorFile[0]];
  for (let r = 1; r < customerFile.length; r++) {
    const row = customerFile[r], values = row.split(","), matches = index.get(ci.map((i) => values[i]).join(","));
    if (matches !== undefined) for (const match of matches) out.push(row + "," + match);
  }
  return out;
}

function joinDataSet(customerFile, processorFile, fieldNames) { return solve(customerFile, processorFile, fieldNames); }

module.exports = solve;
module.exports.joinDataSet = joinDataSet;
