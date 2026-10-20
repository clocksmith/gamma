function countValues(values) {
  const counts = Array.from(values).reduce((counts, value) => counts.set(value, (counts.get(value) || 0) + 1), new Map());
  return counts;
}

function solve(values, other) {
  const counts = countValues(values);
  let result = 0;
  for (const value of other) {
    if (counts.has(value)) result++;
  }
  return result;
}
