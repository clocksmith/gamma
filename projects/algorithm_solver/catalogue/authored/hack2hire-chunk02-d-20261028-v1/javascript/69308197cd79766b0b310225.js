"use strict";
// Hack2Hire 69308197cd79766b0b310225 (Generate Function Profiling Events, level 1) over an INFERRED spec; qualification unknown.

function parseSamples(samples) {
  return samples.map((sample) => {
    const colon = sample.indexOf(":");
    const stack = sample.slice(colon + 1);
    return [Number(sample.slice(0, colon)), stack ? stack.split("->") : []];
  });
}

function solve(samples) {
  const events = [];
  let previous = [];
  for (const [time, stack] of parseSamples(samples)) {
    let common = 0;
    while (common < previous.length && common < stack.length && previous[common] === stack[common]) common++;
    for (let d = previous.length - 1; d >= common; d--) events.push(["end", previous[d], time]);
    for (let d = common; d < stack.length; d++) events.push(["start", stack[d], time]);
    previous = stack;
  }
  return events;
}

function generateEvents(samples) { return solve(samples); }

module.exports = solve;
module.exports.generateEvents = generateEvents;
