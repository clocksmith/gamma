function zValues(text) {
  const values = Array(text.length).fill(0);
  let left = 0;
  let right = 0;
  for (let index = 1; index < text.length; index += 1) {
    if (index < right) {
      values[index] = Math.min(right - index, values[index - left]);
    }
    while (index + values[index] < text.length && text[values[index]] === text[index + values[index]]) {
      values[index] += 1;
    }
    if (index + values[index] > right) {
      left = index;
      right = index + values[index];
    }
  }
  return values;
}


class Solution {
  deleteString(s) {
    const best = Array(s.length + 1).fill(0);
    for (let start = s.length - 1; start >= 0; start -= 1) {
      const suffix = s.slice(start);
      const matches = zValues(suffix);
      best[start] = 1;
      for (let length = 1; length <= Math.floor(suffix.length / 2); length += 1) {
        if (matches[length] >= length) {
          best[start] = Math.max(best[start], 1 + best[start + length]);
        }
      }
    }
    return best[0];
  }
}
