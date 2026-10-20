function topKFrequent(nums, k) {
  const frequencies = new Map();
  for (const number of nums) frequencies.set(number, (frequencies.get(number) || 0) + 1);
  return [...frequencies].sort((left, right) =>
    right[1] - left[1] || left[0] - right[0]
  ).slice(0, k).map(([number]) => number);
}
