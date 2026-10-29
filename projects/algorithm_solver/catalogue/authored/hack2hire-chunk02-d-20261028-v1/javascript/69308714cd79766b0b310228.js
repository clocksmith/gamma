"use strict";
// Hack2Hire 69308714cd79766b0b310228 (Generate Function Profiling Events, level 2) over an INFERRED spec; qualification unknown.

function parseSamples(samples) {
  return samples.map((sample) => {
    const colon = sample.indexOf(":");
    const stack = sample.slice(colon + 1);
    return [Number(sample.slice(0, colon)), stack ? stack.split("->") : []];
  });
}

function solve(samples, minSamples) {
  const keyed = [];
  const open = []; // [name, first sample index, first time]
  let previous = [];
  const rows = parseSamples(samples);
  rows.forEach(([time, stack], index) => {
    let common = 0;
    while (common < previous.length && common < stack.length && previous[common] === stack[common]) common++;
    for (let d = previous.length - 1; d >= common; d--) {
      const [name, first, started] = open.pop();
      if (index - first >= minSamples) {
        keyed.push([started, 1, d, ["start", name, started]]);
        keyed.push([time, 0, -d, ["end", name, time]]);
      }
    }
    for (let d = common; d < stack.length; d++) open.push([stack[d], index, time]);
    previous = stack;
  });
  open.forEach(([name, first, started], d) => {
    if (rows.length - first >= minSamples) keyed.push([started, 1, d, ["start", name, started]]);
  });
  keyed.sort((x, y) => x[0] - y[0] || x[1] - y[1] || x[2] - y[2]);
  return keyed.map((x) => x[3]);
}

function generateEvents(samples, minSamples) { return solve(samples, minSamples); }

module.exports = solve;
module.exports.generateEvents = generateEvents;
