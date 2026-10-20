function maxProfit(prices) {
  let hold = -Infinity, sold = -Infinity, rest = 0;
  for (const price of prices) {
    const nextHold = Math.max(hold, rest - price);
    const nextSold = hold + price;
    const nextRest = Math.max(rest, sold);
    hold = nextHold; sold = nextSold; rest = nextRest;
  }
  return Math.max(rest, sold, 0);
}
