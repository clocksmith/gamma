function countValues(values) {
  const counts = new Map();
  for (const value of values) {
    counts.set(value, (counts.get(value) || 0) + 1);
  }
  return counts;
}

function solve(values) {
    return Math.min(countValues(values).size, Math.floor(values.length / 2));
  }
