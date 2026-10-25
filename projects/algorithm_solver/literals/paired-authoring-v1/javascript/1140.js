class Solution {
  stoneGameII(piles) {
    const size = piles.length;
    if (size === 0) {
      return 0;
    }
    const suffix = Array(size + 1).fill(0);
    for (let index = size - 1; index >= 0; index -= 1) {
      suffix[index] = suffix[index + 1] + piles[index];
    }
    const scores = Array.from({length: size + 1}, () => Array(size + 1).fill(0));
    for (let index = size - 1; index >= 0; index -= 1) {
      for (let limit = 1; limit <= size; limit += 1) {
        if (index + 2 * limit >= size) {
          scores[index][limit] = suffix[index];
        } else {
          let best = 0;
          for (let taken = 1; taken <= 2 * limit; taken += 1) {
            const opponent = scores[index + taken][Math.max(limit, taken)];
            best = Math.max(best, suffix[index] - opponent);
          }
          scores[index][limit] = best;
        }
      }
    }
    return scores[0][1];
  }
}
