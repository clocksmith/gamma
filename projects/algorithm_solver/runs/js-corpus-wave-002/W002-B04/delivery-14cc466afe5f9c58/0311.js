function multiply(mat1, mat2) {
  if (!mat1.length || !mat2.length) return [];
  const rows = mat1.length, columns = mat2[0].length;
  const result = Array.from({ length: rows }, () => Array(columns).fill(0));
  const nonzero = mat2.map(row => row.flatMap((value, column) => value === 0 ? [] : [[column, value]]));
  for (let row = 0; row < rows; row++) for (let k = 0; k < mat1[row].length; k++) {
    const left = mat1[row][k];
    if (left === 0) continue;
    for (const [column, right] of nonzero[k]) result[row][column] += left * right;
  }
  return result;
}
