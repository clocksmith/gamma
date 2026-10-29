"use strict";
// Hack2Hire 692f515ecd79766b0b310123 (Concurrent Web Crawler) over an INFERRED deterministic spec; qualification unknown.
function hostname(url) {
  const rest = url.slice("http://".length), slash = rest.indexOf("/");
  return slash < 0 ? rest : rest.slice(0, slash);
}
function solve(startUrl, links) {
  const host = hostname(startUrl), seen = new Set([startUrl]), queue = [startUrl];
  for (let head = 0; head < queue.length; head++) {
    const url = queue[head];
    const found = Object.prototype.hasOwnProperty.call(links, url) ? links[url] : [];
    for (const next of found) {
      if (!seen.has(next) && hostname(next) === host) { seen.add(next); queue.push(next); }
    }
  }
  return [...seen].sort();
}
function crawl(startUrl, links) { return solve(startUrl, links); }
module.exports = solve;
module.exports.crawl = crawl;
