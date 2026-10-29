// 518 — Coin Change II. Original implementation; authored candidate, not independently qualified.
function solve(amount, coins) {
  const dp=Array(amount+1).fill(0);dp[0]=1;
  for(const coin of coins)for(let value=coin;value<=amount;value++)dp[value]+=dp[value-coin];
  return dp[amount];
}

module.exports = { solve, change: solve };
