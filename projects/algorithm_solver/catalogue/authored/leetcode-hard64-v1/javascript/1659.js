'use strict';

// 1659. Maximize Grid Happiness: rolling ternary-frontier dynamic programming.
// O(m*n*3^w*(I+1)*(E+1)) time and O(3^w*(I+1)*(E+1)) space, w=min(m,n). Inputs are preserved.
function solve(m, n, introvertsCount, extrovertsCount) {
  const width = Math.min(m, n);
  const cells = m * n;
  const introverts = Math.min(introvertsCount, cells);
  const extroverts = Math.min(extrovertsCount, cells);
  const profiles = 3 ** width;
  const upperPlace = 3 ** (width - 1);
  const extrovertStates = extroverts + 1;
  const interaction = [[0, 0, 0], [0, -60, -10], [0, -10, 40]];
  let states = new Map([[0, 0]]);
  for (let position = 0; position < cells; position += 1) {
    const following = new Map();
    function retain(key, value) {
      if (!following.has(key) || value > following.get(key)) following.set(key, value);
    }
    for (const [key, happiness] of states) {
      const population = Math.floor(key / profiles);
      const mask = key % profiles;
      const usedIntroverts = Math.floor(population / extrovertStates);
      const usedExtroverts = population % extrovertStates;
      const upper = Math.floor(mask / upperPlace);
      const left = position % width === 0 ? 0 : mask % 3;
      const shifted = (mask % upperPlace) * 3;
      retain(population * profiles + shifted, happiness);
      if (usedIntroverts < introverts) {
        retain((population + extrovertStates) * profiles + shifted + 1,
          happiness + 120 + interaction[1][upper] + interaction[1][left]);
      }
      if (usedExtroverts < extroverts) {
        retain((population + 1) * profiles + shifted + 2,
          happiness + 40 + interaction[2][upper] + interaction[2][left]);
      }
    }
    states = following;
  }
  let answer = 0;
  for (const value of states.values()) answer = Math.max(answer, value);
  return answer;
}

const getMaxGridHappiness = solve;
class Solution {
  getMaxGridHappiness(m, n, introvertsCount, extrovertsCount) { return solve(m, n, introvertsCount, extrovertsCount); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getMaxGridHappiness };
