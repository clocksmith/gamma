'use strict';

// 3295. Report Spam Message (Easy).
// Specification: https://leetcode.com/problems/report-spam-message/description/
function solve(message, bannedWords) {
  const banned = new Set(bannedWords);
  let matches = 0;
  for (const w of message) if (banned.has(w)) matches++;
  return matches >= 2;
}
const reportSpam = solve;
class Solution { reportSpam(message, bannedWords) { return solve(message, bannedWords); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reportSpam };
