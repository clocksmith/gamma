function solve(values) {
  const counts = {};
  for (const value of values) {
    counts[value] = (counts[value] || 0) + 1;
  }
  let count = 0;
  for (const value2 in counts) {
    const count2 = counts[value2];
    count = helper(count, count2);
  }
  return count >= 2;
}
function helper(values2, other) {
  values2 = Math.abs(values2);
  other = Math.abs(other);
  while (other !== 0) {
    const value3 = values2 % other;
    values2 = other;
    other = value3;
  }
  return values2;
}
