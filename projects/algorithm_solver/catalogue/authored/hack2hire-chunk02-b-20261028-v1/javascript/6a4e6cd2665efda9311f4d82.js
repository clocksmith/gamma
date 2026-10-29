"use strict";
// Original Hack2Hire 6a4e6cd2665efda9311f4d82 variant over an INFERRED specification (injected automaton); qualification unknown.
function solve(input, transitions, start, accepting) {
  let state = start;
  for (let i = 0; i < input.length; i++) state = transitions[state][input[i] === "a" ? 0 : 1];
  return new Set(accepting).has(state);
}
function simulateDfa(input, transitions, start, accepting) { return solve(input, transitions, start, accepting); }
module.exports = solve;
module.exports.simulateDfa = simulateDfa;
