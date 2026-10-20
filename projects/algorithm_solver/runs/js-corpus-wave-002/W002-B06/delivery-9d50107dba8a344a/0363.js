function maxSumSubmatrix(matrix, k) {
  const originalRows = matrix.length;
  const originalColumns = matrix[0].length;
  const shortRows = originalRows <= originalColumns;
  const rows = shortRows ? originalRows : originalColumns;
  const columns = shortRows ? originalColumns : originalRows;
  let best = -Infinity;

  function lowerBound(sorted, value) {
    let low = 0;
    let high = sorted.length;
    while (low < high) {
      const middle = low + Math.floor((high - low) / 2);
      if (sorted[middle] < value) low = middle + 1;
      else high = middle;
    }
    return low;
  }

  for (let top = 0; top < rows; top++) {
    const columnSums = new Array(columns).fill(0);
    for (let bottom = top; bottom < rows; bottom++) {
      const prefixes = [0];
      let prefix = 0;
      for (let column = 0; column < columns; column++) {
        columnSums[column] += shortRows ? matrix[bottom][column] : matrix[column][bottom];
        prefix += columnSums[column];
        prefixes.push(prefix);
      }

      const sorted = [...new Set(prefixes)].sort((left, right) => left - right);
      const tree = new Int32Array(sorted.length + 1);
      function add(position) {
        for (let index = position + 1; index < tree.length; index += index & -index) tree[index]++;
      }
      function sumBefore(position) {
        let count = 0;
        for (let index = position; index > 0; index -= index & -index) count += tree[index];
        return count;
      }
      function findByRank(rank) {
        let position = 0;
        let bit = 1;
        while (bit * 2 < tree.length) bit *= 2;
        for (; bit > 0; bit = Math.floor(bit / 2)) {
          const next = position + bit;
          if (next < tree.length && tree[next] < rank) {
            rank -= tree[next];
            position = next;
          }
        }
        return position;
      }

      add(lowerBound(sorted, 0));
      let inserted = 1;
      for (let index = 1; index < prefixes.length; index++) {
        const current = prefixes[index];
        const smallestAllowed = lowerBound(sorted, current - k);
        const before = sumBefore(smallestAllowed);
        if (before < inserted) {
          const match = sorted[findByRank(before + 1)];
          best = Math.max(best, current - match);
          if (best === k) return k;
        }
        add(lowerBound(sorted, current));
        inserted++;
      }
    }
  }
  return best;
}
