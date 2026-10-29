"use strict";
// Hack2Hire 68ad961ccdaebe9459ce9a83 (Auto Email Generation) over an INFERRED spec; qualification unknown.

function solve(detectedWords, categories, username) {
  const categoryOf = new Map(categories.map(([keyword, category]) => [keyword, category]));
  const grouped = new Map();
  for (const word of detectedWords) {
    const category = categoryOf.get(word);
    if (category === undefined) continue;
    if (!grouped.has(category)) grouped.set(category, new Map());
    const counts = grouped.get(category);
    counts.set(word, (counts.get(word) || 0) + 1);
  }
  const lines = ["Dear " + username + ","];
  if (grouped.size === 0) lines.push("No violations found.");
  for (const category of [...grouped.keys()].sort()) {
    const parts = [];
    for (const [word, count] of grouped.get(category)) parts.push(word + " (" + count + ")");
    lines.push(category + ": " + parts.join(", "));
  }
  return lines.join("\n");
}

function generateEmail(detectedWords, categories, username) { return solve(detectedWords, categories, username); }

module.exports = solve;
module.exports.generateEmail = generateEmail;
