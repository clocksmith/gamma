function letterCounts(text) {
  const counts = Array(26).fill(0);
  const firstCode = "a".charCodeAt(0);
  for (const character of text) {
    counts[character.charCodeAt(0) - firstCode] += 1;
  }
  return counts;
}


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
  numSmallerByFrequency(queries, words) {
    const frequencies = [];
    for (const word of words) {
      const counts = letterCounts(word);
      frequencies.push(counts.find(count => count > 0));
    }
    frequencies.sort((first, second) => first - second);
    const output = [];
    for (const query of queries) {
      const counts = letterCounts(query);
      const frequency = counts.find(count => count > 0);
      const firstGreater = upperBound(frequencies, frequency);
      output.push(frequencies.length - firstGreater);
    }
    return output;
  }
}
