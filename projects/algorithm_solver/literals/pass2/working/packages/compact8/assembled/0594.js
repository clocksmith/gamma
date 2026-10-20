function countValues(values) {
  const counts = new Map();
  for (const value of values) {
    counts.set(value, (counts.get(value) || 0) + 1);
  }
  return counts;
}

function solve(values) {
    const counts = countValues(values);
    let result = 0;
    for (const [value, count] of counts) {
      if (counts.has(value + 1)) result = Math.max(result, count + counts.get(value + 1));
    }
    return result;
  }
