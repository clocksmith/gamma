"use strict";
// Hack2Hire 697c2d6c9731315964cfb048 (Accept-Language Header Matching, variant 1) over an INFERRED spec; qualification unknown.
function solve(header, supported) {
  const present = new Set(supported);
  const emitted = new Set(), result = [];
  for (const raw of header.split(",")) {
    const token = raw.replace(/^ +| +$/g, "");
    const matches = present.has(token) ? [token] : [];
    for (const tag of matches) {
      if (!emitted.has(tag)) { emitted.add(tag); result.push(tag); }
    }
  }
  return result;
}
function parseAcceptLanguage(header, supported) { return solve(header, supported); }
module.exports = solve;
module.exports.parseAcceptLanguage = parseAcceptLanguage;
