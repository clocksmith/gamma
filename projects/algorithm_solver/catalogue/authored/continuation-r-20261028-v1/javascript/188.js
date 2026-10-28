function maxProfit(k, prices) {
  if (k >= Math.floor(prices.length / 2)) {
    let answer = 0;
    for (let i = 1; i < prices.length; i++) answer += Math.max(0, prices[i] - prices[i - 1]);
    return answer;
  }
  let cash = Array(k + 1).fill(0), hold = Array(k + 1).fill(-Infinity);
  for (const price of prices) {
    const nextCash = cash.slice(), nextHold = hold.slice();
    for (let count = 1; count <= k; count++) {
      nextHold[count] = Math.max(hold[count], cash[count - 1] - price);
      nextCash[count] = Math.max(cash[count], hold[count] + price);
    }
    cash = nextCash;
    hold = nextHold;
  }
  return cash[k];
}
module.exports = {maxProfit};
