"use strict";
// Hack2Hire 69753e2817272b5c868d5eb3 (Compute Server Load Scores) over an INFERRED spec; qualification unknown.

const RULE_COST = {LIGHT: 0, STANDARD: 2, HEAVY: 5};

function solve(servers, requests) {
  const scores = new Map(), times = new Map();
  for (const [serverId, base] of servers) { scores.set(serverId, base); times.set(serverId, []); }
  for (const [t, serverId, rule] of requests) {
    if (scores.has(serverId)) {
      scores.set(serverId, scores.get(serverId) + 1 + RULE_COST[rule]);
      times.get(serverId).push(t);
    }
  }
  for (const [serverId, ts] of times) {
    ts.sort((x, y) => x - y);
    let bursts = 0;
    for (let j = 0; j < ts.length; j++) {
      if ((j > 0 && ts[j] - ts[j - 1] <= 60) || (j + 1 < ts.length && ts[j + 1] === ts[j])) bursts++;
    }
    scores.set(serverId, scores.get(serverId) + 3 * bursts);
  }
  return servers.map(([serverId]) => [serverId, scores.get(serverId)]);
}

function computeLoadScores(servers, requests) { return solve(servers, requests); }

module.exports = solve;
module.exports.computeLoadScores = computeLoadScores;
