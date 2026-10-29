"use strict";
// Hack2Hire 6a0b5e8dc84b6e8a3be18bbb (Find Camera Admin User). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

function solve(permissions, cameraId) {
  const holders = new Map(), users = new Set();
  for (const [entity, relation, target] of permissions) {
    if (!holders.has(target)) holders.set(target, []);
    holders.get(target).push(entity);
    if (relation === "cameraOwner" || relation === "groupMember") users.add(entity);
  }
  const seen = new Set([cameraId]), queue = [cameraId];
  for (let head = 0; head < queue.length; head++) {
    for (const entity of holders.get(queue[head]) || []) {
      if (!seen.has(entity)) {
        seen.add(entity);
        queue.push(entity);
      }
    }
  }
  return [...seen].filter((x) => users.has(x)).sort();
}

function findCameraAdmins(permissions, cameraId) { return solve(permissions, cameraId); }
module.exports = solve;
module.exports.findCameraAdmins = findCameraAdmins;
