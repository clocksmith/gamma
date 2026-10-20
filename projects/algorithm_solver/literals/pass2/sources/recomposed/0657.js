function countValues(values) {
  const counts = new Map();
  for (const value of values) {
    counts.set(value, (counts.get(value) || 0) + 1);
  }
  return counts;
}

function solve(values) {
    const counts = countValues(values);
    return (counts.get('U') || 0) === (counts.get('D') || 0)
      && (counts.get('L') || 0) === (counts.get('R') || 0);
  }
