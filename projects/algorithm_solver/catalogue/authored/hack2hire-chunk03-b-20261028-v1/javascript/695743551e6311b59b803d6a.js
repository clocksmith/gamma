"use strict";
// Hack2Hire 695743551e6311b59b803d6a (Neighborhood Party Interval Aggregator, level 1) over an INFERRED spec; qualification unknown.

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
    const intervals = byHood.get(hood).slice().sort((a, b) => (a[0] - b[0]) || (a[1] - b[1]));
    let [start, end] = intervals[0];
    for (let k = 1; k < intervals.length; k++) {
      const [s, e] = intervals[k];
      if (s <= end) { if (e > end) end = e; }
      else { result.push([hood, String(start), String(end)]); start = s; end = e; }
    }
    result.push([hood, String(start), String(end)]);
  }
  return result;
}

function aggregatePartyWindows(partyWindows, geoDataList) { return solve(partyWindows, geoDataList); }

module.exports = solve;
module.exports.aggregatePartyWindows = aggregatePartyWindows;
