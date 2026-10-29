"use strict";
// Hack2Hire 6ab470ffb8a9a175a39ba128 (Guess Number with Delay, level 2) over an INFERRED spec; qualification unknown.

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

function solve(upperBound, delay, secret) { return search(upperBound, delay, secret); }

function findSecretWithDelay(upperBound, delay, secret) { return solve(upperBound, delay, secret); }

module.exports = solve;
module.exports.findSecretWithDelay = findSecretWithDelay;
