'use strict';

// 3680. Generate Schedule.
// O(n^2) time, O(n) auxiliary space excluding the O(n^2) returned schedule.
function solve(n) {
  if (n < 5) return [];
  if (n === 5) {
    const first = [[0, 1], [2, 3], [0, 4], [1, 2], [3, 4],
      [0, 2], [1, 3], [2, 4], [0, 3], [1, 4]];
    const orientation = new Map();
    for (const [a, b] of first) orientation.set(Math.min(a, b) * 5 + Math.max(a, b), [a, b]);
    const answer = first.map(pair => pair.slice());
    for (const [a, b] of first) {
      const left = (a + 2) % 5;
      const right = (b + 2) % 5;
      const [home, away] = orientation.get(Math.min(left, right) * 5 + Math.max(left, right));
      answer.push([away, home]);
    }
    return answer;
  }
  const size = n % 2 === 0 ? n : n + 1;
  const answer = [];
  for (let reverse = 0; reverse < 2; reverse += 1) {
    let players = Array.from({ length: size }, (_, index) => index);
    for (let round = 0; round < size - 1; round += 1) {
      const matches = [];
      for (let index = 0; index < size / 2; index += 1) {
        const a = players[index];
        const b = players[size - index - 1];
        if (a < n && b < n) matches.push(reverse ? [b, a] : [a, b]);
      }
      if (answer.length > 0) {
        const [a, b] = answer[answer.length - 1];
        const selected = matches.findIndex(pair => pair[0] !== a && pair[0] !== b && pair[1] !== a && pair[1] !== b);
        [matches[0], matches[selected]] = [matches[selected], matches[0]];
      }
      answer.push(...matches);
      players = [players[0], players[size - 1], ...players.slice(1, -1)];
    }
  }
  return answer;
}

const generateSchedule = solve;
class Solution {
  generateSchedule(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, generateSchedule };
