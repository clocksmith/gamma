function solve(values, other) {
  const counts = {};
  const items = [];
  for (const value of values) {
    if (!(value in counts)) {
      items.push(value);
    }
    counts[value] = (counts[value] || 0) + 1;
  }
  for (let value2 = -100; value2 < 0; value2 += 1) {
    if (counts[value2]) {
      const count = Math.min(counts[value2], other);
      counts[value2] -= count;
      if (!(-value2 in counts)) {
        items.push(-value2);
      }
      counts[-value2] = (counts[-value2] || 0) + count;
      other -= count;
      if (other === 0) {
        break;
      }
    }
  }
  if (other % 2 !== 0 && (counts[0] || 0) === 0) {
    for (let value3 = 1; value3 <= 100; value3 += 1) {
      if (counts[value3]) {
        counts[value3] -= 1;
        if (!(-value3 in counts)) {
          items.push(-value3);
        }
        counts[-value3] = (counts[-value3] || 0) + 1;
        break;
      }
    }
  }
  let result = 0;
  for (const value4 of items) {
    result += value4 * counts[value4];
  }
  return result;
}
