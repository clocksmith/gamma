function countValues(values) {
  const counts = Array.from(values).reduce((counts, value) => counts.set(value, (counts.get(value) || 0) + 1), new Map());
  return counts;
}

const solve = (values) => {
  const counts = countValues(values);
  for (const value of values) {
    if (counts.get(value) > 1) return value;
  }
  return null;
};
