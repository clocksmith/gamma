function sortedKSum(nums, target, arity) {
  const values = nums.slice().sort((left, right) => left - right);
  const count = values.length;
  const result = [];
  const prefix = [];

  function search(start, remaining, residual) {
    if (remaining === 2) {
      let left = start;
      let right = count - 1;
      while (left < right) {
        const pairSum = values[left] + values[right];
        if (pairSum < residual) {
          left += 1;
        } else if (pairSum > residual) {
          right -= 1;
        } else {
          result.push([...prefix, values[left], values[right]]);
          left += 1;
          right -= 1;
          while (left < right && values[left] === values[left - 1]) {
            left += 1;
          }
          while (left < right && values[right] === values[right + 1]) {
            right -= 1;
          }
        }
      }
      return;
    }

    // Ascending, distinct choices preserve lexicographic tuple order.
    for (let index = start; index <= count - remaining; index += 1) {
      if (index > start && values[index] === values[index - 1]) {
        continue;
      }
      prefix.push(values[index]);
      search(index + 1, remaining - 1, residual - values[index]);
      prefix.pop();
    }
  }

  search(0, arity, target);
  return result;
}

class Solution {
  threeSum(nums) {
    return sortedKSum(nums, 0, 3);
  }
}
