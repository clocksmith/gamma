function increasingTriplet(nums) {
  let smallest = Infinity;
  let secondSmallest = Infinity;

  for (const number of nums) {
    if (number <= smallest) {
      smallest = number;
    } else if (number <= secondSmallest) {
      secondSmallest = number;
    } else {
      return true;
    }
  }
  return false;
}
