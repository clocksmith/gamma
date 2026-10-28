function solve(weight) {
  let maximum = null, answer = 0;
  for (const value of weight) {
    if (maximum !== null && value < maximum) { answer++; maximum = null; }
    else maximum = maximum === null ? value : Math.max(maximum, value);
  }
  return answer;
}

var maxBalancedShipments = solve;
module.exports = solve;
