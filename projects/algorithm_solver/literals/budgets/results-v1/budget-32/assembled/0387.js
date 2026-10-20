function countValues(values) {
  const counts = new Map();
  for (const value of values) {
    counts.set(value, (counts.get(value) || 0) + 1);
  }
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
