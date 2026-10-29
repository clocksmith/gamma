"use strict";
// Hack2Hire 68c4834e97640ed3834dc7ca (Hopscotch) over an INFERRED spec; qualification unknown.

function solve(s, start) {
  const n = s.length;
  if (s[start] === "X") return -1;
  const dist = new Array(n).fill(-1);
  dist[start] = 0;
  const queue = [start];
  let head = 0;
  while (head < queue.length) {
    const i = queue[head++];
    if (i === n - 1) return dist[i];
    const cell = s[i];
    let j = 0;
    while (j < cell.length) {
      const direction = cell[j++];
      let step = 0;
      while (j < cell.length && cell[j] >= "0" && cell[j] <= "9") { step = step * 10 + cell.charCodeAt(j) - 48; j++; }
      if (step === 0) step = 1;
      const target = direction === "R" ? i + step : i - step;
      if (target >= 0 && target < n && dist[target] < 0 && s[target] !== "X") {
        dist[target] = dist[i] + 1;
        queue.push(target);
      }
    }
  }
  return -1;
}

function minJumps(s, start) { return solve(s, start); }

module.exports = solve;
module.exports.minJumps = minJumps;
