class Solution {
  maxProfit(prices) {
    if (prices.length === 0) {
      return 0;
    }

    let first_cost = prices[0];
    let first_profit = 0;
    let second_cost = prices[0];
    let second_profit = 0;
    for (const price of prices) {
      first_cost = Math.min(first_cost, price);
      first_profit = Math.max(first_profit, price - first_cost);
      second_cost = Math.min(second_cost, price - first_profit);
      second_profit = Math.max(second_profit, price - second_cost);
    }
    return second_profit;
  }
}
