'use strict';

// 841. Keys and Rooms (Medium).
// Specification: https://leetcode.com/problems/keys-and-rooms/description/
function solve(rooms) {
  const visited = new Set([0]);
  const stack = [0];
  while (stack.length > 0) {
    const room = stack.pop();
    for (const key of rooms[room]) {
      if (!visited.has(key)) { visited.add(key); stack.push(key); }
    }
  }
  return visited.size === rooms.length;
}
const canVisitAllRooms = solve;
class Solution { canVisitAllRooms(rooms) { return solve(rooms); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canVisitAllRooms };
