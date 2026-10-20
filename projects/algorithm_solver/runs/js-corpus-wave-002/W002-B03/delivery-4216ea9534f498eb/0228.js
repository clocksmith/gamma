function summaryRanges(nums) {
  const result = [];
  for (let i = 0; i < nums.length;) {
    const start = nums[i];
    let end = start;
    while (i + 1 < nums.length && nums[i + 1] === end + 1) end = nums[++i];
    result.push(start === end ? String(start) : `${start}->${end}`);
    i++;
  }
  return result;
}
