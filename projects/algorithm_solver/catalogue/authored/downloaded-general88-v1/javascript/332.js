'use strict';

// 332. Reconstruct Itinerary (Hard).
// Specification: https://leetcode.com/problems/reconstruct-itinerary/description/
function solve(tickets) {
  const graph = {};
  for (const [from, to] of tickets) { if (!graph[from]) graph[from] = []; graph[from].push(to); }
  for (const from in graph) graph[from].sort().reverse();
  const result = [];
  function visit(airport) {
    while (graph[airport] && graph[airport].length > 0) visit(graph[airport].pop());
    result.push(airport);
  }
  visit('JFK');
  return result.reverse();
}
const findItinerary = solve;
class Solution { findItinerary(tickets) { return solve(tickets); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findItinerary };
