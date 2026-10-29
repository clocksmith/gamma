"use strict";
// Hack2Hire 68cdc7ec3735a578b6f27eec (Guess Number) over an INFERRED spec; qualification unknown.

function solve(secret) {
  const log = [];
  const guessNumber = (guess) => {
    log.push(guess);
    let hits = 0;
    for (let i = 0; i < 4; i++) if (guess[i] === secret[i]) hits++;
    return hits;
  };
  const count = new Array(10).fill(0);
  let known = 0;
  for (let digit = 0; digit < 10; digit++) {
    if (known === 4) break;
    if (digit === 9) { count[9] = 4 - known; break; }
    const answer = guessNumber(String(digit).repeat(4));
    count[digit] = answer; known += answer;
    if (answer === 4) return log;
  }
  const filler = String(count.indexOf(0));
  let placed = "";
  for (let position = 0; position < 4; position++) {
    const left = [];
    for (let d = 0; d < 10; d++) if (count[d] > 0) left.push(d);
    let chosen = left[left.length - 1];
    if (left.length > 1) {
      for (let k = 0; k < left.length - 1; k++) {
        if (guessNumber(filler.repeat(position) + left[k] + filler.repeat(3 - position)) === 1) { chosen = left[k]; break; }
      }
    }
    placed += chosen; count[chosen]--;
  }
  if (log[log.length - 1] !== placed) guessNumber(placed);
  return log;
}

function guessTranscript(secret) { return solve(secret); }

module.exports = solve;
module.exports.guessTranscript = guessTranscript;
