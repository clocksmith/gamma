"use strict";
// Hack2Hire 697c2f499731315964cfb056 (Accept-Language Header Matching, variant 2) over an INFERRED spec; qualification unknown.
function solve(header, supported) {
  const present = new Set(supported);
  const byLanguage = new Map();
  for (const tag of supported) {
    const language = tag.slice(0, 2);
    if (!byLanguage.has(language)) byLanguage.set(language, []);
    byLanguage.get(language).push(tag);
  }
  const emitted = new Set(), result = [];
  for (const raw of header.split(",")) {
    const token = raw.replace(/^ +| +$/g, "");
    let matches;
    if (token.length === 2) matches = byLanguage.get(token) || [];
    else matches = present.has(token) ? [token] : [];
    for (const tag of matches) {
      if (!emitted.has(tag)) { emitted.add(tag); result.push(tag); }
    }
  }
  return result;
}
function parseAcceptLanguage(header, supported) { return solve(header, supported); }
module.exports = solve;
module.exports.parseAcceptLanguage = parseAcceptLanguage;
