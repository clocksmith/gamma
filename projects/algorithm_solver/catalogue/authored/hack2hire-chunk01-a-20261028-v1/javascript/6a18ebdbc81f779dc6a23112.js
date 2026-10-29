"use strict";
// Hack2Hire 6a18ebdbc81f779dc6a23112 (Count and Flip Binary Operations) over an INFERRED spec; qualification unknown.
function solve(binaryString, requests) {
  const prefix = new Int32Array(binaryString.length + 1);
  for (let i = 0; i < binaryString.length; i++) prefix[i + 1] = prefix[i] + (binaryString[i] === "1" ? 1 : 0);
  let flipped = false;
  const result = [];
  for (const request of requests) {
    if (request === "flip") { flipped = !flipped; continue; }
    const index = Number(request.slice(6)), ones = prefix[index + 1];
    result.push(flipped ? index + 1 - ones : ones);
  }
  return result;
}
function processRequests(binaryString, requests) { return solve(binaryString, requests); }
module.exports = solve;
module.exports.processRequests = processRequests;
