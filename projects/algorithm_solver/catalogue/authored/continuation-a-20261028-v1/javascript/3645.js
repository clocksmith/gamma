function solve(value, limit) {
  const groups = new Map();
  for (let i = 0; i < value.length; i++) {
    if (!groups.has(limit[i])) groups.set(limit[i], []);
    groups.get(limit[i]).push(value[i]);
  }
  let answer = 0;
  for (const [threshold, amounts] of groups) {
    amounts.sort((a, b) => b - a);
    for (let i = 0; i < Math.min(threshold, amounts.length); i++) answer += amounts[i];
  }
  return answer;
}

var maxTotal = solve;
module.exports = solve;
