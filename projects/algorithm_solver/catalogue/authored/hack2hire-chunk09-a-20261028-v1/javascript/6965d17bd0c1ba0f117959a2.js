"use strict";
// Hack2Hire 6965d17bd0c1ba0f117959a2 (Best Meeting Date by Country) over an INFERRED spec; qualification unknown.

function solve(participants) {
  const counts = new Map();
  for (const [, country, dates] of participants) {
    let per = counts.get(country);
    if (per === undefined) { per = new Map(); counts.set(country, per); }
    for (const d of new Set(dates)) per.set(d, (per.get(d) || 0) + 1);
  }
  const chosen = new Map();
  for (const [country, per] of counts) {
    let bestC = -1, bestD = null;
    for (const [d, c] of per) if (c > bestC || (c === bestC && d < bestD)) { bestC = c; bestD = d; }
    if (bestD !== null) chosen.set(country, bestD);
  }
  const attendees = new Map();
  for (const country of chosen.keys()) attendees.set(country, []);
  for (const [name, country, dates] of participants) {
    if (chosen.has(country) && dates.includes(chosen.get(country))) attendees.get(country).push(name);
  }
  const order = [...chosen.keys()].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
  return order.map((c) => [c, chosen.get(c), attendees.get(c)]);
}

function scheduleMeetings(participants) { return solve(participants); }

module.exports = solve;
module.exports.scheduleMeetings = scheduleMeetings;
