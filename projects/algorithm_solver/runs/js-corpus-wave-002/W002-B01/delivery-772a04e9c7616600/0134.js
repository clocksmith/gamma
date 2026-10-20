function canCompleteCircuit(gas, cost) {
  let totalBalance = 0;
  let routeBalance = 0;
  let candidateStart = 0;

  for (let index = 0; index < gas.length; index += 1) {
    const balance = gas[index] - cost[index];
    totalBalance += balance;
    routeBalance += balance;

    if (routeBalance < 0) {
      candidateStart = index + 1;
      routeBalance = 0;
    }
  }

  return totalBalance < 0 ? -1 : candidateStart;
}
