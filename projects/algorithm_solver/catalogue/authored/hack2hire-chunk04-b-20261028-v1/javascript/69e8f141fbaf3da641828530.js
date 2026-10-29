"use strict";
// Hack2Hire 69e8f141fbaf3da641828530 (Correct Bedroom Counts from Descriptions) over an INFERRED spec; qualification unknown.

// Maximal runs of ASCII letters and digits, lower-cased (descriptions are printable ASCII).
function words(text) { return text.toLowerCase().split(/[^a-z0-9]+/).filter((w) => w.length > 0); }

function classify(text) {
  const w = words(text);
  const studio = w.includes("studio");
  let one = w.some((x) => x === "1br" || x === "1bd");
  for (let i = 0; !one && i + 1 < w.length; i++) if ((w[i] === "1" || w[i] === "one") && w[i + 1] === "bedroom") one = true;
  if (studio && !one) return 0;
  if (one && !studio) return 1;
  return -1;
}

function solve(descriptions, numBedrooms) {
  return descriptions.map((text, i) => {
    const kind = classify(text);
    return kind < 0 ? numBedrooms[i] : kind;
  });
}

function correctBedrooms(descriptions, numBedrooms) { return solve(descriptions, numBedrooms); }

module.exports = solve;
module.exports.correctBedrooms = correctBedrooms;
