function countValues(values) {
  const counts = new Map();
  for (const value of values) {
    counts.set(value, (counts.get(value) || 0) + 1);
  }
  return counts;
}

function solve(values) {
  const counts = countValues(values);
  let result = 0;
  for (const [value, count] of counts) {
    if (count % 2) result ^= value;
  }
  return result;
}
