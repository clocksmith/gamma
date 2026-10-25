class Solution {
  digitsCount(digit, low, high) {
    const countThrough = (bound) => {
      let total = 0;
      let factor = 1;
      while (factor <= bound) {
        const higher = Math.floor(bound / (factor * 10));
        const current = Math.floor(bound / factor) % 10;
        const lower = bound % factor;
        if (digit !== 0) {
          total += higher * factor;
          if (current > digit) {
            total += factor;
          } else if (current === digit) {
            total += lower + 1;
          }
        } else if (higher > 0) {
          total += (higher - 1) * factor;
          total += current === 0 ? lower + 1 : factor;
        }
        factor *= 10;
      }
      return total;
    };
    return countThrough(high) - countThrough(low - 1);
  }
}
