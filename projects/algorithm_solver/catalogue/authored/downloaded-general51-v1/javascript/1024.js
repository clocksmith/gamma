'use strict';

// 1024. Video Stitching (Medium).
// Specification: https://leetcode.com/problems/video-stitching/description/
function solve(clips, time) {
  const sorted = clips.slice().sort((a, b) => a[0] - b[0]);
  let count = 0; let currentEnd = 0; let nextEnd = 0; let index = 0;
  while (currentEnd < time) {
    while (index < sorted.length && sorted[index][0] <= currentEnd) { nextEnd = Math.max(nextEnd, sorted[index][1]); index++; }
    if (nextEnd <= currentEnd) return -1;
    currentEnd = nextEnd;
    count++;
  }
  return count;
}
const videoStitching = solve;
class Solution { videoStitching(clips, time) { return solve(clips, time); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, videoStitching };
