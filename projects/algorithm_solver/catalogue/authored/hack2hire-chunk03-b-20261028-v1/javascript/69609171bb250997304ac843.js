"use strict";
// Hack2Hire 69609171bb250997304ac843 (Neighborhood Party Interval Aggregator, level 2) over an INFERRED spec; qualification unknown.

function group(partyWindows, geoDataList) {
  const window = new Map();
  for (const [party, start, end] of partyWindows) window.set(party, [Number(start), Number(end)]);
  const byHood = new Map();
  for (const [party, hood] of geoDataList) {
    if (!byHood.has(hood)) byHood.set(hood, []);
    byHood.get(hood).push(window.get(party));
  }
  return byHood;
}

// Code point order (all inputs are ASCII, so UTF-16 code unit order matches).
const byCodePoint = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

function solve(partyWindows, geoDataList) {
  const byHood = group(partyWindows, geoDataList), result = [];
  for (const hood of [...byHood.keys()].sort(byCodePoint)) {
    const events = [];
    for (const [s, e] of byHood.get(hood)) { events.push([s, 1]); events.push([e, -1]); }
    events.sort((a, b) => (a[0] - b[0]) || (a[1] - b[1]));  // at equal hours the end (-1) comes first
    let active = 0, peak = 0;
    for (const [, delta] of events) { active += delta; if (active > peak) peak = active; }
    result.push([hood, peak]);
  }
  return result;
}

function peakConcurrentParties(partyWindows, geoDataList) { return solve(partyWindows, geoDataList); }

module.exports = solve;
module.exports.peakConcurrentParties = peakConcurrentParties;
