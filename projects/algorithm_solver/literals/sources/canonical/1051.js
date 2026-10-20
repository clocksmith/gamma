function siftDown(values, index, length) {
  while (index * 2 + 1 < length) {
    let child = index * 2 + 1;
    if (child + 1 < length && values[child] < values[child + 1]) {
      child += 1;
    }
    if (values[index] >= values[child]) {
      return;
    }
    const value = values[index];
    values[index] = values[child];
    values[child] = value;
    index = child;
  }
}
class Solution {
  heightChecker(values) {
    const sorted = values.slice();
    for (let index = Math.floor(sorted.length / 2) - 1; index >= 0; index -= 1) {
      siftDown(sorted, index, sorted.length);
    }
    for (let length = sorted.length - 1; length > 0; length -= 1) {
      const value = sorted[0];
      sorted[0] = sorted[length];
      sorted[length] = value;
      siftDown(sorted, 0, length);
    }
    let result = 0;
    for (let index = 0; index < values.length; index += 1) {
      if (values[index] !== sorted[index]) {
        result += 1;
      }
    }
    return result;
  }
}
