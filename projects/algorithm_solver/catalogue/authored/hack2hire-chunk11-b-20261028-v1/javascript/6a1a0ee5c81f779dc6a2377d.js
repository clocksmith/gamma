"use strict";
// Hack2Hire 6a1a0ee5c81f779dc6a2377d (Implement Dataset Join Operation, variant 3 of 4) over an INFERRED spec; qualification unknown.

function solve(customerFile, processorFile, fieldName) {
  const customerHeader = customerFile[0].split(","), processorHeader = processorFile[0].split(",");
  const ci = customerHeader.indexOf(fieldName), pi = processorHeader.indexOf(fieldName);
  const index = new Map(); // key value -> processor row numbers in input order
  for (let r = 1; r < processorFile.length; r++) {
    const key = processorFile[r].split(",")[pi];
    if (!index.has(key)) index.set(key, []);
    index.get(key).push(r);
  }
  const used = new Array(processorFile.length).fill(false);
  const padding = ",".repeat(processorHeader.length);
  const out = [customerFile[0] + "," + processorFile[0]];
  for (let r = 1; r < customerFile.length; r++) {
    const row = customerFile[r], matches = index.get(row.split(",")[ci]);
    if (matches !== undefined) for (const m of matches) { used[m] = true; out.push(row + "," + processorFile[m]); }
    else out.push(row + padding);
  }
  const lead = ",".repeat(customerHeader.length);
  for (let r = 1; r < processorFile.length; r++) if (!used[r]) out.push(lead + processorFile[r]);
  return out;
}

function joinDataSet(customerFile, processorFile, fieldName) { return solve(customerFile, processorFile, fieldName); }

module.exports = solve;
module.exports.joinDataSet = joinDataSet;
