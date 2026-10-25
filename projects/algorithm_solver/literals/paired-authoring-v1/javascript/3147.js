class Solution {
  maximumEnergy(energy, k) {
    const totals = energy.slice();
    let best = energy[energy.length - 1];
    for (let index = energy.length - 1; index >= 0; index -= 1) {
      if (index + k < energy.length) {
        totals[index] += totals[index + k];
      }
      best = Math.max(best, totals[index]);
    }
    return best;
  }
}
