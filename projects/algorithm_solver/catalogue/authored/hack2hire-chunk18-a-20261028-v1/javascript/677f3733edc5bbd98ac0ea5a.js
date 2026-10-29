"use strict";
// Hack2Hire 677f3733edc5bbd98ac0ea5a (Highway Checkpoint) over an INFERRED spec; qualification unknown.

function position(name) {
  let i = 0;
  while (name[i] < "0" || name[i] > "9") i++;
  return Number(name.slice(i));
}

function solve(records) {
  const state = new Map();
  for (const [plate, checkpoint] of records) {
    const here = position(checkpoint);
    const entry = state.get(plate);
    if (entry === undefined) state.set(plate, [here, 0]);
    else {
      entry[1] += Math.abs(here - entry[0]) * 10;
      entry[0] = here;
    }
  }
  const plates = [...state.keys()].sort();
  return plates.map((plate) => [plate, state.get(plate)[1]]);
}

function calculateTolls(records) { return solve(records); }

module.exports = solve;
module.exports.calculateTolls = calculateTolls;
