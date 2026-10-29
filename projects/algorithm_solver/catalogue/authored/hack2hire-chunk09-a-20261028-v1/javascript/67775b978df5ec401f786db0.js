"use strict";
// Hack2Hire 67775b978df5ec401f786db0 (Ball Picking Game) over an INFERRED spec; qualification unknown.

function solve(balls) {
  const n = balls.length;
  let total = 0;
  for (const v of balls) total += v;
  let prev2 = new Array(n + 1).fill(0); // diff for length L - 2, indexed by left end
  let prev1 = new Array(n + 1).fill(0); // diff for length L - 1
  for (let length = 1; length <= n; length++) {
    const cur = new Array(n + 1).fill(0);
    for (let l = 0; l + length <= n; l++) {
      const r = l + length; // interval balls[l:r]
      let best = balls[l] - prev1[l + 1];
      let x = balls[r - 1] - prev1[l];
      if (x > best) best = x;
      if (length >= 2) {
        x = balls[l] + balls[l + 1] - prev2[l + 2];
        if (x > best) best = x;
        x = balls[r - 1] + balls[r - 2] - prev2[l];
        if (x > best) best = x;
      }
      cur[l] = best;
    }
    prev2 = prev1; prev1 = cur;
  }
  const diff = n ? prev1[0] : 0;
  return (total + diff) / 2; // total + diff is even: it is twice the first player's score
}

function firstPlayerScore(balls) { return solve(balls); }

module.exports = solve;
module.exports.firstPlayerScore = firstPlayerScore;
