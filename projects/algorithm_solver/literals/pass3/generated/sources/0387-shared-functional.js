function countValues(values) {
  const counts = Array.from(values).reduce((counts, value) => counts.set(value, (counts.get(value) || 0) + 1), new Map());
  return counts;
}

function solve(values) {
  const counts = countValues(values);
  for (let result = 0; result < values.length; result++) {
    const value = values[result];
    if (value >= 'a' && value <= 'z' && counts.get(value) === 1) return result;
  }
  return -1;
}
