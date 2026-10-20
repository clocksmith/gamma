function getModifiedArray(length, updates) {
  const difference = new Array(length + 1).fill(0);
  for (const [start, end, increment] of updates) {
    difference[start] += increment;
    difference[end + 1] -= increment;
  }
  const result = new Array(length);
  let current = 0;
  for (let index = 0; index < length; index++) {
    current += difference[index];
    result[index] = current;
  }
  return result;
}
