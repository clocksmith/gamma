function countValues(values) {
  const counts = Array.from(values).reduce((counts, value) => counts.set(value, (counts.get(value) || 0) + 1), new Map());
  return counts;
}

const solve = (values) => {
  const counts = countValues(values);
  return Math.min(counts.size, Math.floor(values.length / 2));
};
