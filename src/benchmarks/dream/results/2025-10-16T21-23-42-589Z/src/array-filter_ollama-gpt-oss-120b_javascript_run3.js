export function customFilter(array, predicate) {
  const result = [];
  for (let i = 0; i < array.length; i++) {
    if (predicate(array[i], i, array)) result.push(array[i]);
  }
  return result;
}