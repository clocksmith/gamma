function largestNumber(nums) {
  const values = nums.map(String);

  values.sort((left, right) => {
    const leftFirst = left + right;
    const rightFirst = right + left;

    if (leftFirst === rightFirst) {
      return 0;
    }
    return leftFirst > rightFirst ? -1 : 1;
  });

  if (values[0] === '0') {
    return '0';
  }

  return values.join('');
}
