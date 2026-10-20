function countValues(values) {
  const counts = Array.from(values).reduce((counts, value) => counts.set(value, (counts.get(value) || 0) + 1), new Map());
  return counts;
}

const solve = (values) => {
  const counts = countValues(values);
  let result = 0;
  for (const [value, count] of counts) {
    if (count % 2) result ^= value;
  }
  return result;
};
