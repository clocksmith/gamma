class Solution {
  assignBikes(workers, bikes) {
    const count = 2 ** bikes.length;
    const costs = new Array(count).fill(Infinity);
    const usedCount = new Array(count).fill(0);
    costs[0] = 0;
    let best = Infinity;
    for (let mask = 0; mask < count; mask += 1) {
      if (mask > 0) {
        usedCount[mask] = usedCount[Math.floor(mask / 2)] + mask % 2;
      }
      const assigned = usedCount[mask];
      if (assigned === workers.length) {
        best = Math.min(best, costs[mask]);
        continue;
      }
      if (assigned > workers.length || costs[mask] === Infinity) {
        continue;
      }
      const worker = workers[assigned];
      for (let index = 0; index < bikes.length; index += 1) {
        const bit = 1 << index;
        if ((mask & bit) === 0) {
          const bike = bikes[index];
          const distance = Math.abs(worker[0] - bike[0]) + Math.abs(worker[1] - bike[1]);
          const nextMask = mask | bit;
          costs[nextMask] = Math.min(costs[nextMask], costs[mask] + distance);
        }
      }
    }
    return best;
  }
}
