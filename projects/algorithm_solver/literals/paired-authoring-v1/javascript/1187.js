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
  makeArrayIncreasing(arr1, arr2) {
    const replacements = Array.from(new Set(arr2)).sort((first, second) => first - second);
    let states = new Map([[-1, 0]]);
    for (const value of arr1) {
      const following = new Map();
      for (const [previous, cost] of states) {
        if (value > previous) {
          following.set(value, Math.min(following.get(value) ?? (arr1.length + 1), cost));
        }
        const index = upperBound(replacements, previous);
        if (index < replacements.length) {
          const replacement = replacements[index];
          following.set(replacement, Math.min(following.get(replacement) ?? (arr1.length + 1), cost + 1));
        }
      }
      if (following.size === 0) {
        return -1;
      }
      states = following;
    }
    let best = arr1.length + 1;
    for (const cost of states.values()) {
      best = Math.min(best, cost);
    }
    return best;
  }
}
