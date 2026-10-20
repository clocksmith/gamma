function generateAbbreviations(word) {
  const result = [];

  function explore(index, pendingCount, current) {
    if (index === word.length) {
      result.push(current + (pendingCount === 0 ? '' : String(pendingCount)));
      return;
    }

    explore(index + 1, pendingCount + 1, current);
    const prefix = current + (pendingCount === 0 ? '' : String(pendingCount));
    explore(index + 1, 0, prefix + word[index]);
  }

  explore(0, 0, '');
  return result;
}
