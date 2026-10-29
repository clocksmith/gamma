// Original hack2hire:6a6d1d1d48af2ae18e99352e; inferred public-preview contract; qualification unknown.
"use strict";
function earliestReachableTime(startX,startY,targetX,targetY,directions) {
  let dx = targetX-startX, dy = targetY-startY;
  if (dx === 0 && dy === 0) return 0;
  for (let i = 0; i < directions.length; i++) {
    const ch = directions[i];
    if (ch === 'E' && dx > 0) dx--; else if (ch === 'W' && dx < 0) dx++;
    else if (ch === 'N' && dy > 0) dy--; else if (ch === 'S' && dy < 0) dy++;
    if (dx === 0 && dy === 0) return i+1;
  }
  return -1;
}

const solve = earliestReachableTime;
module.exports = solve;
module.exports.earliestReachableTime = earliestReachableTime;
module.exports.Solution = class { earliestReachableTime(...args) { return earliestReachableTime(...args); } };
