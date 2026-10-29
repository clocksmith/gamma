"use strict";
// Original Hack2Hire 69f3d14942791c82ab992e68 variant over an INFERRED specification (request helper modelled as an injected map); qualification unknown.
const NOT_FOUND = {message: "Not Found", next: []};
function solve(maze) {
  const request = (url, headers) => (Object.prototype.hasOwnProperty.call(maze, url) ? maze[url] : NOT_FOUND);
  const queue = ["/"], seen = new Set(["/"]);
  for (let head = 0; head < queue.length; head++) {
    const url = queue[head], response = request(url, {});
    if (response.message === "Congrats") return url;
    for (const next of response.next) if (!seen.has(next)) { seen.add(next); queue.push(next); }
  }
  return "";
}
function findMazeExit(maze) { return solve(maze); }
module.exports = solve;
module.exports.findMazeExit = findMazeExit;
