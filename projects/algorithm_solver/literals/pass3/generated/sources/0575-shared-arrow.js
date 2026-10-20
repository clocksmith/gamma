function countValues(values) {
  const counts = new Map();
  for (const value of values) {
    counts.set(value, (counts.get(value) || 0) + 1);
  }
  return counts;
}

const solve = (values) => {
  const counts = countValues(values);
  return Math.min(counts.size, Math.floor(values.length / 2));
};
