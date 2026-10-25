class Solution {
  maxProfit(prices) {
    let profit = 0;
    for (let index = 1; index < prices.length; index += 1) {
      const increase = prices[index] - prices[index - 1];
      if (increase > 0) {
        profit += increase;
      }
    }
    return profit;
  }
}
