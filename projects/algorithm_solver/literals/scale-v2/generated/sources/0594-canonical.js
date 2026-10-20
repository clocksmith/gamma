function solve(values) {
  const counts = helper(values);
  let size = 0;
  for (const value of values) {
    const count = counts[value + 1] || 0;
    if (count > 0) {
      const size2 = counts[value] + count;
      if (size2 > size) {
        size = size2;
      }
    }
  }
  return size;
}
function helper(values2) {
  const counts2 = {};
  for (const value2 of values2) {
    counts2[value2] = (counts2[value2] || 0) + 1;
  }
  return counts2;
}
