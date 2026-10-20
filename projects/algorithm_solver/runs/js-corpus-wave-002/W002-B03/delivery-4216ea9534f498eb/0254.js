function getFactors(n) {
  const result = [];
  function search(remaining, minimum, prefix) {
    for (let factor = minimum; factor * factor <= remaining; factor++) {
      if (remaining % factor !== 0) continue;
      result.push([...prefix, factor, remaining / factor]);
      search(remaining / factor, factor, [...prefix, factor]);
    }
  }
  search(n, 2, []);
  return result;
}
