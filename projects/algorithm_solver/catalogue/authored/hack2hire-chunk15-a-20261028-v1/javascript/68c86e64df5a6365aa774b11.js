"use strict";
// Hack2Hire 68c86e64df5a6365aa774b11 (Campground Carpool) over an INFERRED spec; qualification unknown.

const CAMP = "Campground";

function arrivalTimes(next, start) {
  const times = new Map([[start, 0]]);
  let current = start, now = 0;
  while (current !== CAMP) {
    const [target, duration] = next.get(current);
    now += duration; current = target;
    times.set(current, now);
  }
  return times;
}

function solve(roads, friends, start1, start2) {
  const next = new Map();
  for (const [source, target, duration] of roads) next.set(source, [target, duration]);
  const first = arrivalTimes(next, start1), second = arrivalTimes(next, start2);
  const sides = [[], []];
  friends.forEach(([name, home], index) => {
    const a = first.get(home), b = second.get(home);
    if (b === undefined || (a !== undefined && a <= b)) sides[0].push([a, index, name]);
    else sides[1].push([b, index, name]);
  });
  return sides.map((side) => side.sort((x, y) => x[0] - y[0] || x[1] - y[1]).map((item) => item[2]));
}

function assignFriends(roads, friends, start1, start2) { return solve(roads, friends, start1, start2); }

module.exports = solve;
module.exports.assignFriends = assignFriends;
