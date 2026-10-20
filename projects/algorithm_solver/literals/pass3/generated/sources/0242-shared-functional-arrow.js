function countValues(values) {
  const counts = Array.from(values).reduce((counts, value) => counts.set(value, (counts.get(value) || 0) + 1), new Map());
  return counts;
}

const solve = (values, other) => {
  const counts = countValues(values);
  const result = countValues(other);
  if (counts.size !== result.size) return false;
  for (const [value, count] of counts) {
    if (result.get(value) !== count) return false;
  }
  return true;
};
