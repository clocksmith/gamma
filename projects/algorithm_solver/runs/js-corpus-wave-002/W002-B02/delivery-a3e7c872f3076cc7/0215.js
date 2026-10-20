function findKthLargest(nums, k) {
  const values = nums.slice();
  const target = values.length - k;
  let low = 0;
  let high = values.length - 1;

  while (low <= high) {
    const middle = low + Math.floor((high - low) / 2);
    const candidates = [values[low], values[middle], values[high]];
    candidates.sort((left, right) => left - right);
    const pivot = candidates[1];

    let smaller = low;
    let index = low;
    let larger = high;

    while (index <= larger) {
      if (values[index] < pivot) {
        [values[smaller], values[index]] = [
          values[index],
          values[smaller]
        ];
        smaller += 1;
        index += 1;
      } else if (values[index] > pivot) {
        [values[index], values[larger]] = [
          values[larger],
          values[index]
        ];
        larger -= 1;
      } else {
        index += 1;
      }
    }

    if (target < smaller) {
      high = smaller - 1;
    } else if (target > larger) {
      low = larger + 1;
    } else {
      return values[target];
    }
  }

  return values[target];
}
