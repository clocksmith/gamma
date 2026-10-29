"use strict";
// Hack2Hire 696a84b7cc483345efb1b23c (Tag Groups Complement Finder) over an INFERRED spec; qualification unknown.

function solve(groups, filter) {
  const need = new Set(filter);
  const found = new Set();
  for (const group of groups) {
    const tags = new Set(group);
    let valid = true;
    for (const t of need) if (!tags.has(t)) { valid = false; break; }
    if (valid) for (const t of tags) found.add(t);
  }
  for (const t of need) found.delete(t);
  return Array.from(found).sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
}

function complementTags(groups, filter) { return solve(groups, filter); }

module.exports = solve;
module.exports.complementTags = complementTags;
