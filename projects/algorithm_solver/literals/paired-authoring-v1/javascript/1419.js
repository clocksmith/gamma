class Solution {
  minNumberOfFrogs(croakOfFrogs) {
    const stages = new Map([["c", 0], ["r", 1], ["o", 2], ["a", 3], ["k", 4]]);
    const waiting = Array(4).fill(0);
    let active = 0;
    let peak = 0;
    for (const character of croakOfFrogs) {
      if (!stages.has(character)) {
        return -1;
      }
      const stage = stages.get(character);
      if (stage === 0) {
        waiting[0] += 1;
        active += 1;
        peak = Math.max(peak, active);
      } else {
        if (waiting[stage - 1] === 0) {
          return -1;
        }
        waiting[stage - 1] -= 1;
        if (stage === 4) {
          active -= 1;
        } else {
          waiting[stage] += 1;
        }
      }
    }
    return active === 0 ? peak : -1;
  }
}
