"use strict";
// Hack2Hire 6a4fb090665efda9311f5615 (League Earnings) over an INFERRED spec; qualification unknown.

function solve(leagues, stadiumCapacities, silverwareCounts, targetLeague) {
  const clubs = [];
  for (let i = 0; i < leagues.length; i++) if (leagues[i] === targetLeague) clubs.push(i);
  const c = clubs.length;
  let trophies = 0;
  for (const i of clubs) trophies += silverwareCounts[i];
  let total = 0;
  for (const i of clubs) {
    const own = silverwareCounts[i];
    total += stadiumCapacities[i] * ((c - 1) * own + (trophies - own));
  }
  const matches = c * (c - 1);
  let quotient = Math.floor(total / matches);
  while (quotient * matches > total) quotient--;
  while ((quotient + 1) * matches <= total) quotient++;
  const remainder = total - quotient * matches;
  const cents = quotient * 100 + Math.floor((remainder * 200 + matches) / (2 * matches));
  const fraction = cents % 100;
  return [total, String((cents - fraction) / 100) + "." + (fraction < 10 ? "0" : "") + String(fraction)];
}

function leagueEarnings(leagues, stadiumCapacities, silverwareCounts, targetLeague) {
  return solve(leagues, stadiumCapacities, silverwareCounts, targetLeague);
}

module.exports = solve;
module.exports.leagueEarnings = leagueEarnings;
