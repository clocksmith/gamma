function maxEnvelopes(envelopes) {
  const ordered = envelopes.map(([width, height]) => [width, height]);
  ordered.sort((left, right) => left[0] - right[0] || right[1] - left[1]);
  const smallestTails = [];

  for (const [, height] of ordered) {
    let low = 0;
    let high = smallestTails.length;
    while (low < high) {
      const middle = low + Math.floor((high - low) / 2);
      if (smallestTails[middle] < height) low = middle + 1;
      else high = middle;
    }
    smallestTails[low] = height;
  }
  return smallestTails.length;
}
