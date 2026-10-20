function hIndex(citations) {
  let left = 0, right = citations.length;
  while (left < right) {
    const middle = Math.floor((left + right) / 2);
    if (citations[middle] >= citations.length - middle) right = middle;
    else left = middle + 1;
  }
  return citations.length - left;
}
