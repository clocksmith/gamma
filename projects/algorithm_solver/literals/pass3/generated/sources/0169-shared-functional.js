function countValues(values) {
  const counts = Array.from(values).reduce((counts, value) => counts.set(value, (counts.get(value) || 0) + 1), new Map());
  return counts;
}

function solve(values) {
  const counts = countValues(values);
  for (const [value, count] of counts) {
    if (count > values.length / 2) return value;
  }
  return 0;
}
