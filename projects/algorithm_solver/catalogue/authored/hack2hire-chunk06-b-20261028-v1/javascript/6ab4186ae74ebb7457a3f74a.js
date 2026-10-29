"use strict";
// Hack2Hire 6ab4186ae74ebb7457a3f74a (Guess Number with Delay, level 1) over an INFERRED spec; qualification unknown.

function search(upperBound, delay, secret) {
  const pending = [];
  let calls = 0, head = 0;
  const check = (guess) => {
    calls++;
    pending.push(guess);
    if (pending.length - head <= delay) return "PENDING";
    const old = pending[head++];
    return old === secret ? "CORRECT" : old < secret ? "TOO_LOW" : "TOO_HIGH";
  };
  let lo = 1, hi = upperBound;
  for (;;) {
    const mid = Math.floor((lo + hi) / 2);
    let answer;
    for (let i = 0; i <= delay; i++) answer = check(mid);
    if (answer === "CORRECT") return [mid, calls];
    if (answer === "TOO_LOW") lo = mid + 1; else hi = mid - 1;
  }
}

function solve(upperBound, secret) { return search(upperBound, 1, secret); }

function findSecret(upperBound, secret) { return solve(upperBound, secret); }

module.exports = solve;
module.exports.findSecret = findSecret;
