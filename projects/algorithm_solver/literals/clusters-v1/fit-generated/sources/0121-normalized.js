function maximumSingleTradeProfit(values) {
  if (values.length === 0) {
    return 0;
  }
  let minimumPrice = values[0];
  let maximumProfit = 0;
  for (const priceValue of values) {
    const profitValue = priceValue - minimumPrice;
    if (profitValue > maximumProfit) {
      maximumProfit = profitValue;
    }
    if (priceValue < minimumPrice) {
      minimumPrice = priceValue;
    }
  }
  return maximumProfit;
}
function solve(prices) {
  return maximumSingleTradeProfit(prices);
}
