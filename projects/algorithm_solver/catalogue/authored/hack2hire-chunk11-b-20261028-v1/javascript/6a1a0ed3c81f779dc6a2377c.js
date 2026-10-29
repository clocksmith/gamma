"use strict";
// Hack2Hire 6a1a0ed3c81f779dc6a2377c (Implement Dataset Join Operation, variant 2 of 4) over an INFERRED spec; qualification unknown.

function solve(customerFile, processorFile, fieldName) {
  const ci = customerFile[0].split(",").indexOf(fieldName);
  const processorHeader = processorFile[0].split(",");
  const pi = processorHeader.indexOf(fieldName);
  const index = new Map(); // key value -> processor rows in input order
  for (let r = 1; r < processorFile.length; r++) {
    const key = processorFile[r].split(",")[pi];
    if (!index.has(key)) index.set(key, []);
    index.get(key).push(processorFile[r]);
  }
  const padding = ",".repeat(processorHeader.length);
  const out = [customerFile[0] + "," + processorFile[0]];
  for (let r = 1; r < customerFile.length; r++) {
    const row = customerFile[r], matches = index.get(row.split(",")[ci]);
    if (matches !== undefined) for (const match of matches) out.push(row + "," + match);
    else out.push(row + padding);
  }
  return out;
}

function joinDataSet(customerFile, processorFile, fieldName) { return solve(customerFile, processorFile, fieldName); }

module.exports = solve;
module.exports.joinDataSet = joinDataSet;
