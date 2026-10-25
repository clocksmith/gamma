function upperBound(values, target) {
  let left = 0;
  let right = values.length;
  while (left < right) {
    const middle = left + Math.floor((right - left) / 2);
    if (values[middle] <= target) {
      left = middle + 1;
    } else {
      right = middle;
    }
  }
  return left;
}


class Solution {
  maxTwoEvents(events) {
    const ordered = events.slice().sort((first, second) => first[0] - second[0]);
    const starts = ordered.map(event => event[0]);
    const suffix = Array(ordered.length + 1).fill(0);
    for (let index = ordered.length - 1; index >= 0; index -= 1) {
      suffix[index] = Math.max(suffix[index + 1], ordered[index][2]);
    }
    let best = 0;
    for (const [start, end, value] of ordered) {
      const following = upperBound(starts, end);
      best = Math.max(best, value + suffix[following]);
    }
    return best;
  }
}
