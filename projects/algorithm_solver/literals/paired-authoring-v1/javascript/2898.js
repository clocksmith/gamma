class Solution {
  maxScore(prices) {
    const totals = new Map();
    let best = 0;
    for (let index = 0; index < prices.length; index += 1) {
      const price = prices[index];
      const diagonal = price - index;
      const score = (totals.get(diagonal) || 0) + price;
      totals.set(diagonal, score);
      best = Math.max(best, score);
    }
    return best;
  }
}
