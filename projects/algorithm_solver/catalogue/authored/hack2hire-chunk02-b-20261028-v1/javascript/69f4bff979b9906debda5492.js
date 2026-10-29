"use strict";
// Original Hack2Hire 69f4bff979b9906debda5492 variant over an INFERRED specification (request helper modelled as an injected map); qualification unknown.
const NOT_FOUND = {message: "Not Found", next: []}, UNAUTHORIZED = {message: "Unauthorized", next: []};
const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
function solve(maze) {
  const request = (url, headers) => {
    const entry = own(maze, url) ? maze[url] : NOT_FOUND;
    const required = entry.requiredHeaders || {};
    for (const key of Object.keys(required)) if (!own(headers, key) || headers[key] !== required[key]) return UNAUTHORIZED;
    return entry;
  };
  const queue = [["/", {}]], seen = new Set(["/"]);
  for (let head = 0; head < queue.length; head++) {
    const [url, headers] = queue[head], response = request(url, headers);
    if (response.message === "Congrats") return url;
    const forward = response.headers || {};
    for (const next of response.next) if (!seen.has(next)) { seen.add(next); queue.push([next, forward]); }
  }
  return "";
}
function findMazeExitWithHeaders(maze) { return solve(maze); }
module.exports = solve;
module.exports.findMazeExitWithHeaders = findMazeExitWithHeaders;
