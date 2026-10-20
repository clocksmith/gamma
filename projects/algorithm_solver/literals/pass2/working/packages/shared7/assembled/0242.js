function countValues(values) {
  const counts = new Map();
  for (const value of values) {
    counts.set(value, (counts.get(value) || 0) + 1);
  }
  return counts;
}

function solve(values, other) {
  const counts = countValues(values);
  const result = countValues(other);
  if (counts.size !== result.size) return false;
  for (const [value, count] of counts) {
    if (result.get(value) !== count) return false;
  }
  return true;
}
