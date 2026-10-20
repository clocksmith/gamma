function countValues(values) {
  const counts = new Map();
  for (const value of values) {
    counts.set(value, (counts.get(value) || 0) + 1);
  }
  return counts;
}

function solve(values, other) {
    const counts = countValues(values);
    for (const value of other) {
      counts.set(value, (counts.get(value) || 0) - 1);
    }
    return [...counts.values()].every(value => value === 0);
  }
