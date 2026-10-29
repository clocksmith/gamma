"use strict";
// Hack2Hire 690cf5190a0bc710235894b8 (Call Elevator) over an INFERRED spec; qualification unknown.

function solve(elevators, request) {
  const floor = Number(request[0]), direction = request[1];
  let best = -1, bestDistance = -1;
  for (let i = 0; i < elevators.length; i++) {
    const f = Number(elevators[i][0]), state = elevators[i][1];
    let eligible;
    if (state === "idle") eligible = true;
    else if (state !== direction) eligible = false;
    else if (state === "up") eligible = f <= floor;
    else eligible = f >= floor;
    if (eligible) {
      const distance = f >= floor ? f - floor : floor - f;
      if (best < 0 || distance < bestDistance) { best = i; bestDistance = distance; }
    }
  }
  return best;
}

function callElevator(elevators, request) { return solve(elevators, request); }

module.exports = solve;
module.exports.callElevator = callElevator;
