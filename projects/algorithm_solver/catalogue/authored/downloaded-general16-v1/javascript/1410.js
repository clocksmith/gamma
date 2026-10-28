'use strict';

// 1410. HTML Entity Parser (Medium).
// Specification: https://leetcode.com/problems/html-entity-parser/description/
function solve(text) {
  return text
    .split("&quot;").join('"')
    .split("&apos;").join("'")
    .split("&gt;").join(">")
    .split("&lt;").join("<")
    .split("&frasl;").join("/")
    .split("&amp;").join("&");
}
const entityParser = solve;
class Solution { entityParser(...args) { return solve(...args); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, entityParser };
