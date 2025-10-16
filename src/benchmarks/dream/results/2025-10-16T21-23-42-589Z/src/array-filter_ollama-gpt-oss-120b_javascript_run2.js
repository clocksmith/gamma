export function customFilter(array, predicate) {
  const result = [];
  for (const item of array) {
    if (predicate(item)) result.push(item);
  }
  return result;
}
