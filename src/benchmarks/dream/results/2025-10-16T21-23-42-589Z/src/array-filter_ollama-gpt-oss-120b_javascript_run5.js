export function customFilter(array, predicate) {
  const result = [];
  for (let i = 0; i < array.length; i++) {
    const item = array[i];
    if (predicate(item, i, array)) {
      result.push(item);
    }
  }
  return result;
}
