function countValues(values) {
  const counts = new Map();
  for (const value of values) {
    counts.set(value, (counts.get(value) || 0) + 1);
  }
  return counts;
}

function solve(values) {
  const counts = countValues(values);
  for (const value of values) {
    if (counts.get(value) > 1) return value;
  }
  return null;
}
