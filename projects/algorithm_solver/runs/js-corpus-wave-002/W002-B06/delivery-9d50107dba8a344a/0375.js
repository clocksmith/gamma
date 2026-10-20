function getMoneyAmount(n) {
  const costs = Array.from({ length: n + 2 }, () => new Array(n + 2).fill(0));

  for (let width = 2; width <= n; width++) {
    for (let start = 1; start + width - 1 <= n; start++) {
      const end = start + width - 1;
      let smallestCost = Infinity;
      for (let guess = start; guess <= end; guess++) {
        const worstCase = guess + Math.max(costs[start][guess - 1], costs[guess + 1][end]);
        smallestCost = Math.min(smallestCost, worstCase);
      }
      costs[start][end] = smallestCost;
    }
  }
  return costs[1][n];
}
